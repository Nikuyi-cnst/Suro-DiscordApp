import tempfile
import sqlite3
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import Index


class LevelSystemTests(unittest.TestCase):
	def setUp(self):
		self.temp_dir = tempfile.TemporaryDirectory()
		self.old_level_db_file = Index.LEVEL_DB_FILE
		Index.LEVEL_DB_FILE = Path(self.temp_dir.name) / "levels.db"
		Index.initialize_level_db()

	def tearDown(self):
		Index.LEVEL_DB_FILE = self.old_level_db_file
		self.temp_dir.cleanup()

	def test_crystal_leaf_accumulates_and_level_up_resets_progress(self):
		self.assertEqual(Index.award_user_crystal_leaf(10, 1001, 19), (1, 19, False))
		self.assertEqual(Index.award_user_crystal_leaf(10, 1001, 1), (2, 0, True))
		self.assertEqual(Index.get_user_level(10, 1001), (2, 0))

	def test_each_level_requires_twenty_more_crystal_leaf_than_previous(self):
		self.assertEqual(Index.award_user_crystal_leaf(10, 1002, 20), (2, 0, True))
		self.assertEqual(Index.award_user_crystal_leaf(10, 1002, 39), (2, 39, False))
		self.assertEqual(Index.award_user_crystal_leaf(10, 1002, 1), (3, 0, True))

	def test_excess_crystal_leaf_is_discarded_after_only_one_level_up(self):
		self.assertEqual(Index.award_user_crystal_leaf(10, 1003, 100), (2, 0, True))

	def test_users_and_guilds_have_independent_level_records(self):
		Index.award_user_crystal_leaf(10, 1004, 15)
		Index.award_user_crystal_leaf(20, 1004, 8)

		self.assertEqual(Index.get_user_level(10, 1004), (1, 15))
		self.assertEqual(Index.get_user_level(20, 1004), (1, 8))
		self.assertEqual(Index.get_user_level(10, 1005), (1, 0))

	def test_level_leaderboard_sorts_by_level_then_crystal_leaf_and_is_guild_scoped(self):
		Index.award_user_crystal_leaf(10, 1020, 20)
		Index.award_user_crystal_leaf(10, 1020, 40)
		Index.award_user_crystal_leaf(10, 1020, 15)
		Index.award_user_crystal_leaf(10, 1021, 20)
		Index.award_user_crystal_leaf(10, 1021, 10)
		Index.award_user_crystal_leaf(10, 1022, 19)
		Index.award_user_crystal_leaf(20, 1023, 20)

		self.assertEqual(
			Index.get_level_leaderboard(10),
			[(1020, 3, 15), (1021, 2, 10), (1022, 1, 19)],
		)

	def test_level_leaderboard_respects_requested_limit(self):
		for user_id in range(1030, 1035):
			Index.award_user_crystal_leaf(10, user_id, user_id - 1030)

		self.assertEqual(len(Index.get_level_leaderboard(10, limit=3)), 3)

	def test_maximum_level_is_configurable_and_stops_crystal_leaf_progress(self):
		with patch.object(Index, "MAX_USER_LEVEL", 2):
			self.assertEqual(Index.award_user_crystal_leaf(10, 1006, 20), (2, 0, True))
			self.assertEqual(Index.award_user_crystal_leaf(10, 1006, 100), (2, 0, False))

	def test_resetting_a_user_only_affects_that_user_in_that_guild(self):
		Index.award_user_crystal_leaf(10, 1007, 15)
		Index.award_user_crystal_leaf(20, 1007, 8)

		self.assertTrue(Index.reset_user_level(10, 1007))
		self.assertEqual(Index.get_user_level(10, 1007), (1, 0))
		self.assertEqual(Index.get_user_level(20, 1007), (1, 8))

	def test_resetting_a_guild_does_not_affect_other_guilds(self):
		Index.award_user_crystal_leaf(10, 1008, 15)
		Index.award_user_crystal_leaf(10, 1009, 4)
		Index.award_user_crystal_leaf(20, 1008, 9)

		self.assertEqual(Index.reset_guild_levels(10), 2)
		self.assertEqual(Index.get_user_level(10, 1008), (1, 0))
		self.assertEqual(Index.get_user_level(20, 1008), (1, 9))

	def test_subtracting_levels_resets_crystal_leaf_and_stops_at_level_one(self):
		for reward in (20, 40, 60, 80, 19):
			Index.award_user_crystal_leaf(10, 1010, reward)

		self.assertEqual(Index.subtract_user_levels(10, 1010, 3), (5, 2))
		self.assertEqual(Index.get_user_level(10, 1010), (2, 0))
		self.assertEqual(Index.subtract_user_levels(10, 1010, 5), (2, 1))
		self.assertEqual(Index.get_user_level(10, 1010), (1, 0))

	def test_legacy_global_level_is_claimed_by_first_guild(self):
		connection = sqlite3.connect(Index.LEVEL_DB_FILE)
		connection.execute("DROP TABLE user_levels")
		connection.execute(
			"CREATE TABLE user_levels (user_id INTEGER PRIMARY KEY, level INTEGER NOT NULL, points INTEGER NOT NULL)"
		)
		connection.execute(
			"INSERT INTO user_levels (user_id, level, points) VALUES (?, ?, ?)",
			(1011, 4, 17),
		)
		connection.commit()
		connection.close()

		Index.initialize_level_db()

		self.assertEqual(Index.get_user_level(10, 1011), (4, 17))
		self.assertEqual(Index.get_user_level(20, 1011), (1, 0))

	def test_existing_guild_points_column_is_renamed_without_losing_crystal_leaf(self):
		connection = sqlite3.connect(Index.LEVEL_DB_FILE)
		connection.execute("DROP TABLE user_levels")
		connection.execute(
			"""
			CREATE TABLE user_levels (
				guild_id INTEGER NOT NULL,
				user_id INTEGER NOT NULL,
				level INTEGER NOT NULL,
				points INTEGER NOT NULL,
				PRIMARY KEY (guild_id, user_id)
			)
			"""
		)
		connection.execute(
			"INSERT INTO user_levels (guild_id, user_id, level, points) VALUES (?, ?, ?, ?)",
			(10, 1012, 3, 27),
		)
		connection.commit()
		connection.close()

		Index.initialize_level_db()

		connection = sqlite3.connect(Index.LEVEL_DB_FILE)
		columns = {column[1] for column in connection.execute("PRAGMA table_info(user_levels)")}
		connection.close()
		self.assertIn("crystal_leaf", columns)
		self.assertNotIn("points", columns)
		self.assertEqual(Index.get_user_level(10, 1012), (3, 27))

	def test_lottery_crystal_leaf_reward_occurs_only_below_one_in_ten_thousand(self):
		with (
			patch.object(Index.random, "random", return_value=0.000099),
		):
			self.assertEqual(Index.roll_menu_reward_crystal_leaf(), 100)

		with (
			patch.object(Index.random, "random", return_value=0.0001),
			patch.object(Index.random, "randint", return_value=7),
		):
			self.assertEqual(Index.roll_menu_reward_crystal_leaf(), 7)


class AdminLevelCommandTests(unittest.IsolatedAsyncioTestCase):
	async def test_all_level_management_commands_reject_non_admins(self):
		response = SimpleNamespace(send_message=AsyncMock())
		interaction = SimpleNamespace(
			guild_id=10,
			user=SimpleNamespace(id=1001),
			response=response,
		)
		target_user = SimpleNamespace(id=1002, mention="<@1002>")
		command_calls = (
			(Index.reset_user_level_command, (target_user,)),
			(Index.reset_guild_levels_command, ()),
			(Index.subtract_level_command, (target_user, 2)),
		)

		with patch.object(Index, "is_menu_admin", return_value=False):
			for command, arguments in command_calls:
				await cast(Any, command.callback)(interaction, *arguments)

		self.assertEqual(response.send_message.await_count, 3)
		self.assertTrue(
			all("관리자만" in call.args[0] for call in response.send_message.await_args_list)
		)


if __name__ == "__main__":
	unittest.main()