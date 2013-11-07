# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import unittest
import webnotes

class TestItem(unittest.TestCase):
	def test_duplicate_item(self):
		from stock.doctype.item_price.item_price import ItemPriceDuplicateItem
		bean = webnotes.bean(copy=test_records[0])
		self.assertRaises(ItemPriceDuplicateItem, bean.insert)

test_records = [
	[
		{
			"doctype": "Item Price",
			"price_list": "_Test Price List",
			"item_code": "_Test Item",
			"ref_rate": 100
		}
	],
	[
		{
			"doctype": "Item Price",
			"price_list": "_Test Price List Rest of the World",
			"item_code": "_Test Item 2",
			"ref_rate": 123
		}
	],
	[
		{
			"doctype": "Item Price",
			"price_list": "_Test Price List Rest of the World",
			"item_code": "_Test Item Home Desktop 100",
			"ref_rate": 25
		}
	],
	[
		{
			"doctype": "Item Price",
			"price_list": "_Test Price List Rest of the World",
			"item_code": "_Test Item Home Desktop 200",
			"ref_rate": 7999
		}
	],
]