import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import Index


class ActivityScheduleTests(unittest.TestCase):
	def test_activity_candidates_follow_kst_schedule_boundaries(self):
		cases = (
			(datetime(2026, 10, 8, 7, 59, tzinfo=Index.KST), None),
			(datetime(2026, 10, 8, 8, 0, tzinfo=Index.KST), (1,)),
			(datetime(2026, 10, 8, 11, 0, tzinfo=Index.KST), (2, 3, 4)),
			(datetime(2026, 10, 8, 13, 0, tzinfo=Index.KST), (5, 6, 7, 8)),
			(datetime(2026, 10, 8, 18, 0, tzinfo=Index.KST), (2, 3, 8, 9)),
			(datetime(2026, 10, 8, 20, 0, tzinfo=Index.KST), None),
		)

		for current_time, expected_ids in cases:
			with self.subTest(current_time=current_time):
				period = Index.get_activity_period(current_time)
				self.assertEqual(period[0] if period else None, expected_ids)

	def test_rare_activity_is_selected_only_below_half_percent_threshold(self):
		with patch.object(Index.random, "random", return_value=0.004):
			self.assertEqual(Index.choose_activity_id((2, 3, 4)), 4)

		with patch.object(Index.random, "random", return_value=0.005):
			self.assertIn(Index.choose_activity_id((2, 3, 4)), (2, 3))

	def test_selection_avoids_previous_activity_when_alternatives_exist(self):
		self.assertEqual(Index.choose_activity_id((2, 3), previous_activity_id=2), 3)

	def test_single_activity_period_keeps_its_only_activity(self):
		self.assertEqual(Index.choose_activity_id((1,), previous_activity_id=1), 1)


class ActivityUpdateTests(unittest.IsolatedAsyncioTestCase):
	async def test_activity_duration_is_capped_at_next_schedule_boundary(self):
		bot = Index.ComicWorldBot(None)
		bot.change_presence = AsyncMock()
		current_time = datetime(2026, 10, 8, 12, 30, tzinfo=Index.KST)

		with (
			patch.object(Index, "datetime") as datetime_mock,
			patch.object(Index.random, "random", return_value=1),
			patch.object(Index.random, "choice", return_value=2),
			patch.object(Index.random, "randint", return_value=3),
		):
			datetime_mock.now.return_value = current_time
			await bot.update_activity.coro(bot)

		self.assertEqual(
			bot.activity_deadline,
			datetime(2026, 10, 8, 13, 0, tzinfo=Index.KST),
		)
		presence_call = bot.change_presence.await_args
		if presence_call is None:
			self.fail("활동 상태 변경이 호출되지 않았습니다.")
		self.assertEqual(presence_call.kwargs["activity"].name, Index.Activitys[2])

	async def test_night_clears_presence(self):
		bot = Index.ComicWorldBot(None)
		bot.change_presence = AsyncMock()
		bot.activity_id = 9
		current_time = datetime(2026, 10, 8, 20, 0, tzinfo=Index.KST)

		with patch.object(Index, "datetime") as datetime_mock:
			datetime_mock.now.return_value = current_time
			await bot.update_activity.coro(bot)

		bot.change_presence.assert_awaited_once_with(activity=None)
		self.assertIsNone(bot.activity_id)
		self.assertIsNone(bot.activity_deadline)


if __name__ == "__main__":
	unittest.main()