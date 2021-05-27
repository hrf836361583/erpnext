# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import os
import json

import frappe
from frappe import _


def setup_taxes_and_charges(company_name: str, country: str):
	if not frappe.db.exists('Company', company_name):
		frappe.throw(_('Company {} does not exist yet. Taxes setup aborted.').format(company_name))

	file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'country_wise_tax.json')
	with open(file_path, 'r') as json_file:
		tax_data = json.load(json_file)

	country_wise_tax = tax_data.get(country)

	if not country_wise_tax:
		return

	if 'chart_of_accounts' not in country_wise_tax:
		country_wise_tax = simple_to_detailed(country_wise_tax)

	from_detailed_data(company_name, country_wise_tax.get('chart_of_accounts'))


def simple_to_detailed(templates):
	"""
	Convert a simple taxes object into a more detailed data structure.

	Example input:

	{
		"France VAT 20%": {
			"account_name": "VAT 20%",
			"tax_rate": 20,
			"default": 1
		},
		"France VAT 10%": {
			"account_name": "VAT 10%",
			"tax_rate": 10
		}
	}
	"""
	return {
		'chart_of_accounts': {
			'*': {
				'item_tax_templates': [{
					'title': title,
					'taxes': [{
						'tax_type': {
							'account_name': data.get('account_name'),
							'tax_rate': data.get('tax_rate')
						}
					}]
				} for title, data in templates.items()],
				'*': [{
					'title': title,
					'is_default': data.get('default', 0),
					'taxes': [{
						'account_head': {
							'account_name': data.get('account_name'),
							'tax_rate': data.get('tax_rate')
						}
					}]
				} for title, data in templates.items()]
			}
		}
	}


def from_detailed_data(company_name, data):
	"""Create Taxes and Charges Templates from detailed data."""
	coa_name = frappe.db.get_value('Company', company_name, 'chart_of_accounts')
	tax_templates = data.get(coa_name) or data.get('*')
	sales_tax_templates = tax_templates.get('sales_tax_templates') or tax_templates.get('*')
	purchase_tax_templates = tax_templates.get('purchase_tax_templates') or tax_templates.get('*')
	item_tax_templates = tax_templates.get('item_tax_templates') or tax_templates.get('*')

	if sales_tax_templates:
		for template in sales_tax_templates:
			make_taxes_and_charges_template(company_name, 'Sales Taxes and Charges Template', template)

	if purchase_tax_templates:
		for template in purchase_tax_templates:
			make_taxes_and_charges_template(company_name, 'Purchase Taxes and Charges Template', template)

	if item_tax_templates:
		for template in item_tax_templates:
			make_item_tax_template(company_name, template)


def make_taxes_and_charges_template(company_name, doctype, template):
	template['company'] = company_name
	template['doctype'] = doctype

	if frappe.db.exists(doctype, {'title': template.get('title'), 'company': company_name}):
		return

	for tax_row in template.get('taxes'):
		account_data = tax_row.get('account_head')
		tax_row_defaults = {
			'category': 'Total',
			'charge_type': 'On Net Total'
		}

		# if account_head is a dict, search or create the account and get it's name
		if isinstance(account_data, dict):
			tax_row_defaults['description'] = '{0} @ {1}'.format(account_data.get('account_name'), account_data.get('tax_rate'))
			tax_row_defaults['rate'] = account_data.get('tax_rate')
			account = get_or_create_account(company_name, account_data)
			tax_row['account_head'] = account.name

		# use the default value if nothing other is specified
		for fieldname, default_value in tax_row_defaults.items():
			if fieldname not in tax_row:
				tax_row[fieldname] = default_value

	return frappe.get_doc(template).insert(ignore_permissions=True)


def make_item_tax_template(company_name, template):
	"""Create an Item Tax Template.

	This requires a separate method because Item Tax Template is structured
	differently from Sales and Purchase Tax Templates.
	"""
	doctype = 'Item Tax Template'
	template['company'] = company_name
	template['doctype'] = doctype

	if frappe.db.exists(doctype, {'title': template.get('title'), 'company': company_name}):
		return

	for tax_row in template.get('taxes'):
		account_data = tax_row.get('tax_type')

		# if tax_type is a dict, search or create the account and get it's name
		if isinstance(account_data, dict):
			account = get_or_create_account(company_name, account_data)
			tax_row['tax_type'] = account.name
			if 'tax_rate' not in tax_row:
				tax_row['tax_rate'] = account_data.get('tax_rate')

	return frappe.get_doc(template).insert(ignore_permissions=True)


def get_or_create_account(company_name, account):
	"""
	Check if account already exists. If not, create it.
	Return a tax account or None.
	"""
	default_root_type = 'Liability'
	root_type = account.get('root_type', default_root_type)

	existing_accounts = frappe.get_list('Account',
		filters={
			'company': company_name,
			'root_type': root_type
		},
		or_filters={
			'account_name': account.get('account_name'),
			'account_number': account.get('account_number')
		}
	)

	if existing_accounts:
		return frappe.get_doc('Account', existing_accounts[0].name)

	tax_group = get_or_create_tax_group(company_name, root_type)

	account['doctype'] = 'Account'
	account['company'] = company_name
	account['parent_account'] = tax_group
	account['report_type'] = 'Balance Sheet'
	account['account_type'] = 'Tax'
	account['root_type'] = root_type
	account['is_group'] = 0

	return frappe.get_doc(account).insert(ignore_permissions=True, ignore_mandatory=True)


def get_or_create_tax_group(company_name, root_type):
	# Look for a group account of type 'Tax'
	tax_group_name = frappe.db.get_value('Account', {
		'is_group': 1,
		'root_type': root_type,
		'account_type': 'Tax',
		'company': company_name
	})

	if tax_group_name:
		return tax_group_name

	# Look for a group account named 'Duties and Taxes' or 'Tax Assets'
	account_name = _('Duties and Taxes') if root_type == 'Liability' else _('Tax Assets')
	tax_group_name = frappe.db.get_value('Account', {
		'is_group': 1,
		'root_type': root_type,
		'account_name': account_name,
		'company': company_name
	})

	if tax_group_name:
		return tax_group_name

	# Create a new group account named 'Duties and Taxes' or 'Tax Assets' just
	# below the root account
	root_account = frappe.get_list('Account', {
		'is_group': 1,
		'root_type': root_type,
		'company': company_name,
		'report_type': 'Balance Sheet',
		'parent_account': ('is', 'not set')
	}, limit=1)[0]

	tax_group_account = frappe.get_doc({
		'doctype': 'Account',
		'company': company_name,
		'is_group': 1,
		'report_type': 'Balance Sheet',
		'root_type': root_type,
		'account_type': 'Tax',
		'account_name': account_name,
		'parent_account': root_account.name
	}).insert(ignore_permissions=True)

	tax_group_name = tax_group_account.name

	return tax_group_name
