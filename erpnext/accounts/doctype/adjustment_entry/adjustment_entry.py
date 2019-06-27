# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.party import get_party_account
from erpnext.accounts.utils import get_outstanding_invoices
from erpnext.setup.utils import get_exchange_rate

class AdjustmentEntry(AccountsController):
    def get_unreconciled_entries(self):
        self.check_mandatory_to_fetch()
        self.get_entries()

    def check_mandatory_to_fetch(self):
        for fieldname in self.get_mandatory_fields():
            if not self.get(fieldname):
                frappe.throw(_("Please select {0} first").format(self.meta.get_label(fieldname)))

    def get_mandatory_fields(self):
        mandatory_fields = ["company", "adjustment_type"]
        if self.adjustment_type != 'Purchase':
            mandatory_fields.append("customer")
        if self.adjustment_type != 'Sales':
            mandatory_fields.append("supplier")
        return mandatory_fields

    def get_exchange_rates(self, entries):
        currencies = list(set([entry.get("currency") for entry in entries]))
        if self.payment_currency not in currencies:
            currencies.append(self.payment_currency)
        self.set('exchange_rates', [])
        for currency in currencies:
            exc = self.append('exchange_rates', {})
            exc.currency = currency
            exc.exchange_rate_to_payment_currency = get_exchange_rate(currency, self.payment_currency) or 1
            exc.exchange_rate_to_base_currency = get_exchange_rate(currency, self.company_currency) or 1

    def exchange_rates_to_dict(self):
        rates = {}
        for exchange_rate in self.exchange_rates:
            rates[exchange_rate.currency] = {
                "exchange_rate_to_payment_currency": exchange_rate.exchange_rate_to_payment_currency,
                "exchange_rate_to_base_currency": exchange_rate.exchange_rate_to_base_currency
            }
        return rates

    def get_entries(self):
        if self.adjustment_type == 'Sales':
            sales_invoices = self.get_invoices('debit_entries')
            payments = self.get_received_payments()
            self.get_exchange_rates(sales_invoices + payments)
            self.add_invoice_entries(sales_invoices, 'debit_entries')
        elif self.adjustment_type == 'Purchase':
            purchase_invoices = self.get_invoices('credit_entries')
            payments = self.get_paid_payments()
            self.get_exchange_rates(payments + purchase_invoices)
            self.add_invoice_entries(purchase_invoices, 'credit_entries')
        else:
            sales_invoices = self.get_invoices('debit_entries')
            purchase_invoices = self.get_invoices('credit_entries')
            self.get_exchange_rates(sales_invoices+purchase_invoices)
            self.add_invoice_entries(sales_invoices, 'debit_entries')
            self.add_invoice_entries(purchase_invoices, 'credit_entries')

    def get_invoices(self, field_name):
        if field_name == 'debit_entries':
            party_type = "Customer"
            party = self.customer
        else:
            party_type = "Supplier"
            party = self.supplier
        account = get_party_account(party_type, party, self.company)
        non_reconciled_invoices = get_outstanding_invoices(party_type, party, account)
        self.get_extra_invoice_details(non_reconciled_invoices)
        return non_reconciled_invoices

    def get_extra_invoice_details(self, outstanding_invoices):
        for d in outstanding_invoices:
            d["exchange_rate"] = 1
            if d.voucher_type in ("Sales Invoice", "Purchase Invoice"):
                d["exchange_rate"], d["currency"], d["cost_center"] = frappe.db.get_value(d.voucher_type, d.voucher_no, ["conversion_rate", "currency", "cost_center"])
            if d.voucher_type in ("Purchase Invoice"):
                d["supplier_bill_no"], d["supplier_bill_date"] = frappe.db.get_value(d.voucher_type, d.voucher_no, ["bill_no", "bill_date"])

    def get_received_payments(self):
        print("Received")
        return []

    def get_paid_payments(self):
        print("paid")
        return []

    def add_invoice_entries(self, invoices, field_name):
        exchange_rates = self.exchange_rates_to_dict()
        self.set(field_name, [])

        for invoice in invoices:
            ent = self.append(field_name, {})
            ent.voucher_type = invoice.get('voucher_type')
            ent.voucher_number = invoice.get('voucher_no')
            ent.voucher_date = invoice.get('posting_date')
            ent.voucher_base_amount = invoice.get('outstanding_amount')
            ent.currency = invoice.get("currency")
            ent.exchange_rate = invoice.get('exchange_rate')
            ent.cost_center = invoice.get('cost_center')
            ent.voucher_amount = ent.voucher_base_amount / ent.exchange_rate
            ent.payment_exchange_rate = exchange_rates[ent.currency]['exchange_rate_to_payment_currency']
            ent.voucher_payment_amount = ent.voucher_amount * ent.payment_exchange_rate
            ent.balance = ent.voucher_payment_amount
            ent.supplier_bill_no = invoice.get('supplier_bill_no')
            ent.supplier_bill_date = invoice.get('supplier_bill_date')

    def recalculate_tables(self):
        debit_entries = self.debit_entries
        credit_entries = self.credit_entries
        self.get_exchange_rates(debit_entries + credit_entries)
        self.recalculate_references(['debit_entries', 'credit_entries'])

    def recalculate_references(self, reference_types):
        exchange_rates = self.exchange_rates_to_dict()
        for reference_type in reference_types:
            entries = self.get(reference_type)
            if entries:
                for ent in entries:
                    ent.recalculate_amounts(exchange_rates)

    def allocate_amount_to_references(self):
        total_debit_outstanding = sum([flt(d.voucher_payment_amount) for d in self.get("debit_entries")])
        total_credit_outstanding = sum([flt(c.voucher_payment_amount) for c in self.get("credit_entries")])
        exchange_rates = self.exchange_rates_to_dict()
        # total_deductions = sum([flt(d.amount) for d in self.get("deductions")])
        allocate_order = ['credit_entries', 'debit_entries'] if total_debit_outstanding > total_credit_outstanding else ['debit_entries', 'credit_entries']
        for reference_type in allocate_order:
            allocated_oustanding = min(total_debit_outstanding, total_credit_outstanding)
            entries = self.get(reference_type)
            for ent in entries:
                ent.allocated_amount = 0
                if self.allocate_payment_amount:
                    if allocated_oustanding > 0:
                        if ent.voucher_payment_amount >= allocated_oustanding:
                            ent.allocated_amount = allocated_oustanding
                        else:
                            ent.allocated_amount = ent.voucher_payment_amount
                        allocated_oustanding -= flt(ent.allocated_amount)
                ent.recalculate_amounts(exchange_rates)

