import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import Index


class ItemShopTests(unittest.TestCase):
	def setUp(self):
		self.temp_dir = tempfile.TemporaryDirectory()
		self.old_level_db_file = Index.LEVEL_DB_FILE
		Index.LEVEL_DB_FILE = Path(self.temp_dir.name) / "levels.db"
		Index.initialize_level_db()

	def tearDown(self):
		Index.LEVEL_DB_FILE = self.old_level_db_file
		self.temp_dir.cleanup()

	def test_purchase_fails_without_enough_crystal_leaf_and_changes_nothing(self):
		Index.award_user_crystal_leaf(10, 2001, 10)

		was_purchased, balance, daily_limit_reached, purchases_today = Index.buy_shop_item(
			10,
			2001,
			"집문서",
		)

		self.assertFalse(was_purchased)
		self.assertEqual(balance, 10)
		self.assertFalse(daily_limit_reached)
		self.assertEqual(purchases_today, 0)
		self.assertEqual(Index.get_user_level(10, 2001), (1, 10))
		self.assertEqual(Index.get_user_inventory(10, 2001), [])

	def test_purchase_deducts_crystal_leaf_but_preserves_level(self):
		Index.award_user_crystal_leaf(10, 2002, 20)
		Index.award_user_crystal_leaf(10, 2002, 30)

		was_purchased, balance, daily_limit_reached, purchases_today = Index.buy_shop_item(
			10,
			2002,
			"소화제",
		)

		self.assertTrue(was_purchased)
		self.assertEqual(balance, 10)
		self.assertFalse(daily_limit_reached)
		self.assertEqual(purchases_today, 1)
		self.assertEqual(Index.get_user_level(10, 2002), (2, 10))
		self.assertEqual(Index.get_user_inventory(10, 2002), [("소화제", 1)])

	def test_repeated_purchases_increase_inventory_quantity(self):
		unlimited_item = {"price": 5, "description": "test", "daily_limit": 0}
		with (
			patch.dict(Index.ITEM_LIST, {"unlimited": unlimited_item}),
			patch.object(Index, "LEVEL_UP_CRYSTAL_LEAF_PER_LEVEL", 100),
		):
			Index.award_user_crystal_leaf(10, 2003, 65)

			self.assertTrue(Index.buy_shop_item(10, 2003, "unlimited")[0])
			self.assertTrue(Index.buy_shop_item(10, 2003, "unlimited")[0])
		self.assertEqual(Index.get_user_inventory(10, 2003), [("unlimited", 2)])
		self.assertEqual(Index.get_user_level(10, 2003), (1, 55))

	def test_inventory_is_separate_between_guilds(self):
		Index.award_user_crystal_leaf(10, 2004, 20)
		Index.award_user_crystal_leaf(10, 2004, 20)
		self.assertTrue(Index.buy_shop_item(10, 2004, "소화제")[0])

		self.assertEqual(Index.get_user_inventory(10, 2004), [("소화제", 1)])
		self.assertEqual(Index.get_user_inventory(20, 2004), [])

	def test_item_descriptions_appear_in_shop_and_inventory(self):
		shop = Index.make_goldy_shop_embed()
		inventory = Index.format_inventory_items([("소화제", 1)])

		self.assertIn(Index.ITEM_LIST["소화제"]["description"], shop.description)
		self.assertIn(Index.ITEM_LIST["소화제"]["description"], inventory)
		self.assertIn("하루 1회", shop.description)

	def test_daily_limit_blocks_purchase_without_spending_crystal_leaf(self):
		limited_item = {"price": 5, "description": "test", "daily_limit": 1}
		with (
			patch.dict(Index.ITEM_LIST, {"limited": limited_item}),
			patch.object(Index, "LEVEL_UP_CRYSTAL_LEAF_PER_LEVEL", 100),
		):
			Index.award_user_crystal_leaf(10, 2005, 20)
			first_purchase = Index.buy_shop_item(10, 2005, "limited")
			second_purchase = Index.buy_shop_item(10, 2005, "limited")

		self.assertEqual(first_purchase, (True, 15, False, 1))
		self.assertEqual(second_purchase, (False, 15, True, 1))
		self.assertEqual(Index.get_user_level(10, 2005), (1, 15))
		self.assertEqual(Index.get_user_inventory(10, 2005), [("limited", 1)])

	def test_zero_daily_limit_allows_unlimited_purchases(self):
		unlimited_item = {"price": 1, "description": "test", "daily_limit": 0}
		with (
			patch.dict(Index.ITEM_LIST, {"unlimited": unlimited_item}),
			patch.object(Index, "LEVEL_UP_CRYSTAL_LEAF_PER_LEVEL", 100),
		):
			Index.award_user_crystal_leaf(10, 2006, 10)
			first_purchase = Index.buy_shop_item(10, 2006, "unlimited")
			second_purchase = Index.buy_shop_item(10, 2006, "unlimited")

		self.assertEqual(first_purchase, (True, 9, False, 1))
		self.assertEqual(second_purchase, (True, 8, False, 2))
		self.assertEqual(Index.get_user_inventory(10, 2006), [("unlimited", 2)])

	def test_shop_and_inventory_commands_are_registered(self):
		self.assertEqual(Index.goldy_shop_command.name, "골디상점")
		self.assertEqual(Index.inventory_command.name, "인벤토리")


if __name__ == "__main__":
	unittest.main()
