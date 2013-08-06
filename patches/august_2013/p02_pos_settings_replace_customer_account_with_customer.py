# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd.
# License: GNU General Public License v3. See license.txt

import webnotes

def execute():
	customer_account = webnotes.conn.sql("""select customer_account, name from `tabPOS Setting` 
		where ifnull(customer_account, '')!=''""")
	webnotes.reload_doc("accounts", "doctype", "pos_setting")

	for cust_acc, pos_name in customer_account:
		customer = webnotes.conn.sql("""select master_name, account_name from `tabAccount` 
			where name=%s""", (cust_acc), as_dict=1)

		if not customer[0].master_name:
			customer_name = webnotes.conn.get_value('Customer', customer[0].account_name, 'name')
		else:
			customer_name = customer[0].master_name

		webnotes.conn.set_value('POS Setting', pos_name, 'customer', customer_name)