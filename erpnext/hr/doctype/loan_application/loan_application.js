// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

{% include 'erpnext/hr/loan_common.js' %};

frappe.ui.form.on('Loan Application', {
	refresh: function(frm) {
		frm.trigger("toggle_fields")
		frm.trigger("add_toolbar_buttons")
	},
	repayment_method: function(frm) {
		frm.doc.repayment_amount = frm.doc.repayment_periods = ""
		frm.trigger("toggle_fields")
	},
	toggle_fields: function(frm) {
		frm.toggle_enable("repayment_amount", frm.doc.repayment_method=="Repay Fixed Amount per Period")
		frm.toggle_enable("repayment_periods", frm.doc.repayment_method=="Repay Over Number of Periods")
	},
	add_toolbar_buttons: function(frm) {
		if (frm.doc.status == "Approved") {
			frm.add_custom_button(__('Loan'), function() {
				frappe.call({
					type: "GET",
					method: "erpnext.hr.doctype.loan_application.loan_application.make_loan",
					args: {
						"source_name": frm.doc.name
					},
					callback: function(r) {
						if(!r.exc) {
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", r.message.doctype, r.message.name);
						}
					}
				});
			})
		}
	},
	loan_type: function(frm){
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Loan Type",
				fieldname: "rate_of_interest",
				filters: {
					name:["=", frm.doc.loan_type]
					}           			
			},		
			callback: function(r) {
				if(r.message.rate_of_interest){
					frm.set_value('rate_of_interest', r.message.rate_of_interest)
				}
			}
		});
	}
});
