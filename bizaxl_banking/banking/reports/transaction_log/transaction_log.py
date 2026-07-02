# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


def execute(filters=None):
	columns = [
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
		{"label": "Account", "fieldname": "account", "fieldtype": "Link", "options": "Banking Account", "width": 150},
		{"label": "Debit (₹)", "fieldname": "debit_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Credit (₹)", "fieldname": "credit_amount", "fieldtype": "Currency", "width": 120},
		{"label": "Running Balance (₹)", "fieldname": "running_balance", "fieldtype": "Currency", "width": 150},
		{"label": "UTR", "fieldname": "utr_number", "fieldtype": "Data", "width": 160},
		{"label": "Payment Rail", "fieldname": "payment_rail", "fieldtype": "Data", "width": 80},
		{"label": "Settled At", "fieldname": "settled_at", "fieldtype": "Datetime", "width": 150}
	]

	date_filter = filters.get("posting_date") or today()
	account_filter = filters.get("account")

	conditions = "WHERE btl.posting_date = %s"
	params = [date_filter]

	if account_filter:
		conditions += " AND btl.account = %s"
		params.append(account_filter)

	data = frappe.db.sql(f"""
		SELECT
			btl.posting_date,
			btl.account,
			btl.debit_amount,
			btl.credit_amount,
			btl.running_balance,
			po.utr_number,
			po.payment_rail,
			po.settled_at
		FROM `tabBanking Transaction Ledger` btl
		LEFT JOIN `tabBanking Payment Order` po ON po.name = btl.source_docname 
			AND btl.source_doctype = 'Banking Payment Order'
		{conditions}
		ORDER BY btl.creation DESC
	""", params, as_dict=True)

	return columns, data
