# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	if not filters: filters = {}
	columns= [_("Date") + "::240", _("No Debit Note") + "::240", _("Amount") + ":Currency:120", _("Party Name") + "::240", _("Remarks") + "::240"] 
	data = return_data(filters)
	return columns, data

def return_data(filters):
	data = []

	if filters.get("from_date"): from_date = filters.get("from_date")
	if filters.get("to_date"): to_date = filters.get("to_date")

	conditions = return_filters(filters, from_date, to_date)

	payments = frappe.get_all("Bank Transactions", ["*"], filters = conditions)

	for pay in payments:
		row = [pay.check_date_nd, pay.next_note_nd, pay.amount_nd, pay.person_name, pay.movement_detail]
		data.append(row)

	return data

def return_filters(filters, from_date, to_date):
	conditions = ''	

	conditions += "{"
	conditions += '"check_date_nd": ["between", ["{}", "{}"]]'.format(from_date, to_date)
	# conditions += ', "company": "{}"'.format(filters.get("company"))
	conditions += ', "bank_account": "{}"'.format(filters.get("account"))
	conditions += ', "debit_note": 1'
	# conditions += ', "docstatus": 1'
	conditions += '}'

	return conditions
