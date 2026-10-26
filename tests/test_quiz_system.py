import sys
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import Index


class QuizSystemTests(unittest.TestCase):
	def setUp(self):
		self.temp_dir = tempfile.TemporaryDirectory()
		self.old_level_db_file = Index.LEVEL_DB_FILE
		Index.LEVEL_DB_FILE = Path(self.temp_dir.name) / "levels.db"
		Index.initialize_level_db()

	def tearDown(self):
		Index.LEVEL_DB_FILE = self.old_level_db_file
		self.temp_dir.cleanup()

	def create_quiz(self, guild_id: int = 10) -> str:
		session_id = Index.create_quiz_session(
			guild_id,
			2001,
			"테스트 문제",
			"정답",
			"테스트 힌트",
		)
		self.assertIsNotNone(session_id)
		return session_id

	def test_default_quiz_bank_has_three_questions_with_expected_fields(self):
		self.assertEqual(len(Index.quizs), 3)
		for quiz in Index.quizs.values():
			self.assertEqual(
				set(quiz),
				{"<출제자>", "<문제내용>", "<정답>", "<힌트>"},
			)
			self.assertTrue(all(quiz.values()))

	def test_only_one_quiz_can_be_active_per_guild_and_custom_question_is_saved(self):
		Index.save_quiz_question(10, 2001, "테스트 문제", "정답", "테스트 힌트")
		session_id = self.create_quiz()

		self.assertIsNone(
			Index.create_quiz_session(10, 2002, "새 문제", "새 정답", "새 힌트")
		)
		self.assertEqual(Index.get_active_quiz_session(10), session_id)
		self.assertEqual(
			Index.get_quiz_question_bank(10),
			[(2001, "테스트 문제", "정답", "테스트 힌트")],
		)
		other_guild_session = self.create_quiz(guild_id=20)
		self.assertNotEqual(other_guild_session, session_id)

	def test_wrong_answers_are_limited_to_three_per_user_without_ending_quiz(self):
		session_id = self.create_quiz()

		self.assertEqual(Index.submit_quiz_answer(session_id, 3001, "오답"), ("incorrect", 2, 0))
		self.assertEqual(Index.submit_quiz_answer(session_id, 3001, "오답"), ("incorrect", 1, 0))
		self.assertEqual(Index.submit_quiz_answer(session_id, 3001, "오답"), ("incorrect", 0, 0))
		self.assertEqual(Index.submit_quiz_answer(session_id, 3001, "정답"), ("exhausted", 0, 0))
		self.assertEqual(Index.get_active_quiz_session(10), session_id)
		self.assertEqual(Index.submit_quiz_answer(session_id, 3002, "정답")[:2], ("correct", 2))
		self.assertIsNone(Index.get_active_quiz_session(10))

	def test_correct_answer_ends_quiz_for_everyone(self):
		session_id = self.create_quiz()

		with patch.object(Index.random, "randint", return_value=7):
			result = Index.submit_quiz_answer(session_id, 3001, "  정답  ")
		self.assertEqual(result[:2], ("correct", 2))
		self.assertEqual(result[2], 7)
		self.assertGreaterEqual(result[2], Index.QUIZ_REWARD_MIN)
		self.assertLessEqual(result[2], Index.QUIZ_REWARD_MAX)
		self.assertEqual(Index.get_user_level(10, 3001)[1], result[2])
		self.assertEqual(Index.submit_quiz_answer(session_id, 3002, "정답"), ("inactive", 0, 0))
		self.assertEqual(Index.get_quiz_session(session_id), (10, 2001, "solved", "정답"))

	def test_giving_up_ends_the_shared_quiz_and_reveals_answer(self):
		session_id = self.create_quiz()

		self.assertEqual(Index.give_up_quiz(session_id, 3001), ("abandoned", "정답"))
		self.assertEqual(Index.submit_quiz_answer(session_id, 3002, "정답"), ("inactive", 0, 0))
		self.assertEqual(Index.give_up_quiz(session_id, 3003), ("inactive", None))

	def test_first_hint_is_free_second_costs_fifteen_without_changing_level(self):
		Index.award_user_crystal_leaf(10, 3001, 20)
		Index.award_user_crystal_leaf(10, 3001, 35)
		session_id = self.create_quiz()

		self.assertEqual(Index.consume_quiz_hint(10, session_id, 3001), ("free", "테스트 힌트", 0))
		self.assertEqual(Index.consume_quiz_hint(10, session_id, 3001), ("paid", "테스트 힌트", 20))
		self.assertEqual(Index.get_user_level(10, 3001), (2, 20))
		self.assertEqual(Index.consume_quiz_hint(10, session_id, 3001), ("used", None, 0))

	def test_insufficient_hint_balance_does_not_deduct_elif_or_level(self):
		Index.award_user_crystal_leaf(10, 3002, 14)
		session_id = self.create_quiz()
		Index.consume_quiz_hint(10, session_id, 3002)

		self.assertEqual(
			Index.consume_quiz_hint(10, session_id, 3002),
			("insufficient", None, 14),
		)
		self.assertEqual(Index.get_user_level(10, 3002), (1, 14))
		self.assertEqual(Index.consume_quiz_hint(10, session_id, 3002), ("insufficient", None, 14))

	def test_hint_use_and_attempts_are_separate_between_users(self):
		session_id = self.create_quiz()

		self.assertEqual(Index.consume_quiz_hint(10, session_id, 3001)[0], "free")
		self.assertEqual(Index.consume_quiz_hint(10, session_id, 3002)[0], "free")
		self.assertEqual(Index.submit_quiz_answer(session_id, 3001, "오답"), ("incorrect", 2, 0))
		self.assertEqual(Index.submit_quiz_answer(session_id, 3002, "정답")[:2], ("correct", 2))

	def test_quiz_start_cooldown_is_shared_by_guild_and_expires_after_four_hours(self):
		now = 1_800_000_000.0
		status, first_session, remaining = Index.start_quiz_session(
			10, 2001, "첫 문제", "정답", "힌트", now=now
		)
		self.assertEqual((status, remaining), ("started", 0))
		self.assertIsNotNone(first_session)
		Index.give_up_quiz(first_session, 3001)

		status, session_id, remaining = Index.start_quiz_session(
			10, 2002, "두 번째 문제", "정답", "힌트", now=now + 1
		)
		self.assertEqual((status, session_id), ("cooldown", None))
		self.assertEqual(remaining, Index.QUIZ_COOLDOWN_SECONDS - 1)
		self.assertEqual(
			Index.start_quiz_session(
				20, 2002, "다른 서버 문제", "정답", "힌트", now=now + 1
			)[0],
			"started",
		)
		self.assertEqual(
			Index.start_quiz_session(
				10,
				2002,
				"다시 시작",
				"정답",
				"힌트",
				now=now + Index.QUIZ_COOLDOWN_SECONDS,
			)[0],
			"started",
		)

	def test_quiz_reward_is_applied_once_to_winning_user_balance(self):
		session_id = self.create_quiz()
		with patch.object(Index.random, "randint", return_value=17):
			result = Index.submit_quiz_answer(session_id, 3001, "정답")

		self.assertEqual(result, ("correct", 2, 17))
		self.assertEqual(Index.get_user_level(10, 3001), (1, 17))
		self.assertEqual(Index.submit_quiz_answer(session_id, 3002, "정답"), ("inactive", 0, 0))
		self.assertEqual(Index.get_user_level(10, 3002), (1, 0))

	def test_quiz_leaderboard_counts_solved_questions_per_user_and_guild(self):
		with patch.object(Index.random, "randint", return_value=5):
			for user_id in (3001, 3001, 3002):
				session_id = self.create_quiz()
				self.assertEqual(
					Index.submit_quiz_answer(session_id, user_id, "정답")[0],
					"correct",
				)
			for _ in range(3):
				session_id = self.create_quiz(guild_id=20)
				self.assertEqual(
					Index.submit_quiz_answer(session_id, 3001, "정답")[0],
					"correct",
				)

		self.assertEqual(
			Index.get_quiz_leaderboard(10),
			[(3001, 2), (3002, 1)],
		)
		self.assertEqual(Index.get_quiz_leaderboard(20), [(3001, 3)])

	def test_quiz_leaderboard_respects_limit(self):
		with patch.object(Index.random, "randint", return_value=5):
			for user_id in (3001, 3002, 3003):
				session_id = self.create_quiz()
				Index.submit_quiz_answer(session_id, user_id, "정답")

		self.assertEqual(len(Index.get_quiz_leaderboard(10, limit=2)), 2)

	def test_quiz_leaderboard_uses_solved_winner_index(self):
		connection = sqlite3.connect(Index.LEVEL_DB_FILE)
		try:
			query_plan = connection.execute(
				"""
				EXPLAIN QUERY PLAN
				SELECT winner_id, COUNT(*) AS solved_count
				FROM quiz_sessions
				WHERE guild_id = ? AND status = 'solved' AND winner_id IS NOT NULL
				GROUP BY winner_id
				ORDER BY solved_count DESC, winner_id ASC
				LIMIT ?
				""",
				(10, 10),
			).fetchall()
		finally:
			connection.close()

		self.assertTrue(
			any("idx_quiz_solved_winners" in row[3] for row in query_plan),
			query_plan,
		)

	def test_active_quiz_message_metadata_is_saved_for_restart_restoration(self):
		session_id = self.create_quiz()
		Index.save_quiz_message_id(session_id, 4001, 5001)

		self.assertEqual(Index.get_active_quiz_messages(), [(session_id, 4001, 5001)])

	def test_quiz_commands_and_controls_are_registered_and_persistent(self):
		view = Index.QuizView("quiz-session")

		self.assertEqual(Index.start_quiz_command.name, "퀴즈")
		self.assertEqual(Index.submit_quiz_question_command.name, "문제출제")
		self.assertIsNone(view.timeout)
		self.assertEqual(
			[item.custom_id for item in view.children],
			["quiz:hint:v1", "quiz:answer:v1", "quiz:give-up:v1"],
		)


class QuizComponentTests(unittest.IsolatedAsyncioTestCase):
	async def asyncSetUp(self):
		self.temp_dir = tempfile.TemporaryDirectory()
		self.old_level_db_file = Index.LEVEL_DB_FILE
		Index.LEVEL_DB_FILE = Path(self.temp_dir.name) / "levels.db"
		Index.initialize_level_db()
		self.session_id = Index.create_quiz_session(
			10,
			2001,
			"테스트 문제",
			"정답",
			"테스트 힌트",
		)
		self.assertIsNotNone(self.session_id)

	async def asyncTearDown(self):
		Index.LEVEL_DB_FILE = self.old_level_db_file
		self.temp_dir.cleanup()

	async def test_hint_button_sends_a_private_hint_that_expires_after_ten_seconds(self):
		interaction = SimpleNamespace(
			guild_id=10,
			user=SimpleNamespace(id=3001),
			response=SimpleNamespace(send_message=AsyncMock()),
		)
		view = Index.QuizView(self.session_id)

		await view.children[0].callback(interaction)

		interaction.response.send_message.assert_awaited_once()
		kwargs = interaction.response.send_message.await_args.kwargs
		self.assertTrue(kwargs["ephemeral"])
		self.assertEqual(kwargs["delete_after"], 10)
		self.assertIn("테스트 힌트", interaction.response.send_message.await_args.args[0])

	async def test_give_up_button_ends_the_quiz_for_everyone(self):
		interaction = SimpleNamespace(
			user=SimpleNamespace(id=3001, mention="<@3001>"),
			response=SimpleNamespace(edit_message=AsyncMock()),
		)
		view = Index.QuizView(self.session_id)

		await view.children[2].callback(interaction)

		interaction.response.edit_message.assert_awaited_once()
		kwargs = interaction.response.edit_message.await_args.kwargs
		self.assertIn("모두의 퀴즈 풀이가 종료", kwargs["content"])
		self.assertIsNone(kwargs["view"])
		self.assertIsNone(Index.get_active_quiz_session(10))

	async def test_submitting_question_only_saves_it_without_starting_quiz(self):
		Index.cancel_quiz_session(self.session_id)
		interaction = SimpleNamespace(
			guild_id=10,
			user=SimpleNamespace(id=3001),
			response=SimpleNamespace(send_message=AsyncMock()),
		)

		await Index.submit_quiz_question_command.callback(
			interaction,
			"나중에 풀 문제",
			"예시 정답",
			"예시 힌트",
		)

		self.assertIsNone(Index.get_active_quiz_session(10))
		self.assertEqual(
			Index.get_quiz_question_bank(10),
			[(3001, "나중에 풀 문제", "예시 정답", "예시 힌트")],
		)
		interaction.response.send_message.assert_awaited_once()
		self.assertTrue(interaction.response.send_message.await_args.kwargs["ephemeral"])
		self.assertIn(
			"바로 시작하지는 않았어요",
			interaction.response.send_message.await_args.args[0],
		)

	async def test_quiz_command_uses_server_cooldown_and_requested_message(self):
		now = time.time()
		connection = sqlite3.connect(Index.LEVEL_DB_FILE)
		try:
			connection.execute(
				"""
				INSERT INTO quiz_guild_cooldowns (guild_id, session_id, started_at)
				VALUES (?, ?, ?)
				""",
				(10, self.session_id, now - Index.QUIZ_COOLDOWN_SECONDS + 60),
			)
			connection.commit()
		finally:
			connection.close()

		interaction = SimpleNamespace(
			guild_id=10,
			user=SimpleNamespace(id=3001),
			response=SimpleNamespace(send_message=AsyncMock()),
		)
		await Index.start_quiz_command.callback(interaction)

		interaction.response.send_message.assert_awaited_once()
		self.assertEqual(
			interaction.response.send_message.await_args.args[0],
			"1시간 뒤에 퀴즈를 풀 수 있어요.",
		)

	async def test_quiz_ranking_command_displays_solved_problem_counts(self):
		Index.cancel_quiz_session(self.session_id)
		with patch.object(Index.random, "randint", return_value=5):
			for user_id in (3001, 3001, 3002):
				session_id = Index.create_quiz_session(
					10, 2001, "테스트 문제", "정답", "테스트 힌트"
				)
				Index.submit_quiz_answer(session_id, user_id, "정답")
		members = {
			3001: SimpleNamespace(mention="<@3001>"),
			3002: SimpleNamespace(mention="<@3002>"),
		}
		interaction = SimpleNamespace(
			guild_id=10,
			guild=SimpleNamespace(get_member=members.get),
			user=SimpleNamespace(id=3001),
			response=SimpleNamespace(send_message=AsyncMock()),
		)

		await Index.ranking_command.callback(
			interaction,
			Index.app_commands.Choice(name="퀴즈랭킹", value="quiz"),
		)

		interaction.response.send_message.assert_awaited_once()
		embed = interaction.response.send_message.await_args.kwargs["embed"]
		self.assertEqual(embed.title, "퀴즈 랭킹")
		self.assertIn("<@3001>", embed.description)
		self.assertIn("정답 **2문제**", embed.description)
		self.assertIn("정답 **1문제**", embed.description)


if __name__ == "__main__":
	unittest.main()
