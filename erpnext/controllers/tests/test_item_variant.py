from __future__ import unicode_literals

import frappe
import json
import unittest

from erpnext.stock.doctype.item.test_item import set_item_variant_settings
from erpnext.controllers.item_variant import copy_attributes_to_variant, make_variant_item_code

from six import string_types

class TestItemVariant(unittest.TestCase):
	def test_tables_in_template_copied_to_variant(self):
		fields = [{'field_name': 'quality_inspection_template'}]
		set_item_variant_settings(fields)
		variant = make_item_variant()
		self.assertEqual(variant.get("quality_inspection_template"), "_Test QC Template")

def create_variant_with_tables(item, args):
	if isinstance(args, string_types):
		args = json.loads(args)

	qc_name = make_quality_inspection_template()
	template = frappe.get_doc("Item", item)
	template.quality_inspection_template = qc_name
	template.save()

	variant = frappe.new_doc("Item")
	variant.variant_based_on = 'Item Attribute'
	variant_attributes = []

	for d in template.attributes:
		variant_attributes.append({
			"attribute": d.attribute,
			"attribute_value": args.get(d.attribute)
		})

	variant.set("attributes", variant_attributes)
	copy_attributes_to_variant(template, variant)
	make_variant_item_code(template.item_code, template.item_name, variant)

	return variant

def make_item_variant():
	if frappe.db.exists("Item", "_Test Variant Item-S"):
		variant = frappe.get_doc("Item", "_Test Variant Item-S")
	else:
		variant = create_variant_with_tables("_Test Variant Item", '{"Test Size": "Small"}')
		variant.item_code = "_Test Variant Item-S"
		variant.item_name = "_Test Variant Item-S"
		variant.save()
	return variant

def make_quality_inspection_template():
	qc_template = "_Test QC Template"
	if frappe.db.exists("Quality Inspection Template", qc_template):
		return qc_template

	qc = frappe.new_doc("Quality Inspection Template")
	qc.quality_inspection_template_name = qc_template
	qc.append('item_quality_inspection_parameter', {
		"specification": "Moisture",
		"value": "&lt; 5%",
	})

	qc.insert()
	return qc.name
