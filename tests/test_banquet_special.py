import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import Index


class BanquetSpecialTests(unittest.TestCase):
	def setUp(self):
		self.temp_dir = tempfile.TemporaryDirectory()
		self.old_level_db_file = Index.LEVEL_DB_FILE
		Index.LEVEL_DB_FILE = Path(self.temp_dir.name) / "levels.db"
		Index.initialize_level_db()

	def tearDown(self):
		Index.LEVEL_DB_FILE = self.old_level_db_file
		self.temp_dir.cleanup()

	def test_menu_pool_adds_level_15_foods_at_level_15(self):
		self.assertEqual(Index.get_banquet_specials(9), Index.eliasFoodsP20)
		self.assertEqual(
			Index.get_banquet_specials(14),
			Index.eliasFoodsP20 + Index.eliasFoodsP30,
		)
		self.assertEqual(
			Index.get_banquet_specials(15),
			Index.eliasFoodsP20 + Index.eliasFoodsP30 + Index.eliasFoodsP40,
		)
		self.assertEqual(
			Index.get_banquet_specials(20),
			Index.eliasFoodsP20 + Index.eliasFoodsP30 + Index.eliasFoodsP40 + Index.eliasFoodsP50,
		)
		self.assertEqual(
			Index.get_banquet_specials(25),
			Index.eliasFoodsP20
			+ Index.eliasFoodsP30
			+ Index.eliasFoodsP40
			+ Index.eliasFoodsP50
			+ Index.eliasFoodsP60,
		)

	def test_level_18_prefers_p40_with_twenty_percent_more_weight(self):
		with (
			patch.object(Index.random, "choices", side_effect=lambda tiers, weights, k: [tiers[-1]]) as choose_tier,
			patch.object(Index.random, "choice", side_effect=lambda foods: foods[-1]),
		):
			self.assertIn(Index.choose_banquet_special(18), Index.eliasFoodsP40)

		self.assertEqual(
			choose_tier.call_args.kwargs["weights"],
			[1.0, 1.0, 1.2],
		)

	def test_level_100_prefers_p60_with_twenty_percent_more_weight(self):
		with (
			patch.object(Index.random, "choices", side_effect=lambda tiers, weights, k: [tiers[-1]]) as choose_tier,
			patch.object(Index.random, "choice", side_effect=lambda foods: foods[-1]),
		):
			self.assertIn(Index.choose_banquet_special(100), Index.eliasFoodsP60)

		self.assertEqual(
			choose_tier.call_args.kwargs["weights"],
			[1.0, 1.0, 1.0, 1.0, 1.2],
		)

	def test_special_reward_uses_selected_tier_base_plus_or_minus_five(self):
		with (
			patch.object(Index.random, "choices", side_effect=lambda tiers, weights, k: [tiers[-1]]),
			patch.object(Index.random, "choice", side_effect=lambda foods: foods[0]),
			patch.object(Index.random, "randint", side_effect=(-5, 4)),
		):
			p20_food, p20_base = Index.choose_banquet_special_reward(1)
			p50_food, p50_base = Index.choose_banquet_special_reward(20)
			self.assertEqual(Index.roll_banquet_special_crystal_leaf(p20_base), 15)
			self.assertEqual(Index.roll_banquet_special_crystal_leaf(p50_base), 54)

		self.assertIn(p20_food, Index.eliasFoodsP20)
		self.assertIn(p50_food, Index.eliasFoodsP50)
		self.assertEqual((p20_base, p50_base), (20, 50))
		with patch.object(Index.random, "randint", return_value=5):
			self.assertEqual(Index.roll_banquet_special_crystal_leaf(20), 25)
			self.assertEqual(Index.roll_banquet_special_crystal_leaf(50), 55)

	def test_banquet_recommendation_also_shows_crystal_leaf_progress(self):
		recommendation = "오늘 메뉴는 고민할 것도 없이 **해초 샐러드**을(를) 먹어봐요."
		progress_message = "-# +22엘리프 (Lv.18 엘리프: 42/360)"
		with (
			patch.object(Index.random, "random", return_value=1),
			patch.object(Index.random, "choice", return_value=recommendation),
		):
			message = Index.format_menu_recommendation_response(
				"연회장 특식",
				"해초 샐러드",
				progress_message,
				is_banquet_special=True,
			)

		self.assertEqual(message, f"{recommendation}\n{progress_message}")

	def test_first_daily_use_is_free_then_each_extra_use_consumes_medicine(self):
		current_date = date(2026, 10, 9)
		Index.award_user_crystal_leaf(10, 3001, 20)
		Index.award_user_crystal_leaf(10, 3001, 20)
		self.assertTrue(Index.buy_shop_item(10, 3001, "소화제")[0])

		self.assertEqual(Index.consume_banquet_special_use(10, 3001, current_date), (True, False))
		self.assertEqual(Index.consume_banquet_special_use(10, 3001, current_date), (True, True))
		self.assertEqual(Index.get_user_inventory(10, 3001), [])
		self.assertEqual(Index.consume_banquet_special_use(10, 3001, current_date), (False, False))

	def test_daily_free_use_resets_on_next_kst_date(self):
		first_date = date(2026, 10, 9)
		self.assertEqual(Index.consume_banquet_special_use(10, 3002, first_date), (True, False))
		self.assertEqual(
			Index.consume_banquet_special_use(10, 3002, first_date + timedelta(days=1)),
			(True, False),
		)


if __name__ == "__main__":
	unittest.main()