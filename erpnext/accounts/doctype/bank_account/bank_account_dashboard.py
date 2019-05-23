from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'fieldname': 'bank_account',
		'non_standard_fieldnames': {
			'Customer': 'default_bank_account',
			'Supplier': 'default_bank_account',
			'Journal Entry': 'bank_account_no'
		},
		'transactions': [
			{
				'label': _('Payments'),
				'items': ['Payment Entry', 'Payment Request', 'Payment Order']
			},
			{
				'label': _('Party'),
				'items': ['Customer', 'Supplier']
			},
			{
				'label': _('Banking'),
				'items': ['Bank Guarantee']
			},
			{
				'label': _('Journal Entries'),
				'items': ['Journal Entry']
			}
		]
	}