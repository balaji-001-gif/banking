# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


def execute(filters=None):
	columns = [
		{"label": "Payment Ref", "fieldname": "payment_ref", "fieldtype": "Data", "width": 160},
		{"label": "Account", "fieldname": "from_account", "fieldtype": "Link", "options": "Banking Account", "width": 150},
		{"label": "Amount (₹)", "fieldname": "amount", "fieldtype": "Currency", "width": 120},
		{"label": "Rail", "fieldname": "payment_rail", "fieldtype": "Data", "width": 80},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "UTR", "fieldname": "utr_number", "fieldtype": "Data", "width": 160},
		{"label": "Settled At", "fieldname": "settled_at", "fieldtype": "Datetime", "width": 150},
		{"label": "Ledger Posted", "fieldname": "ledger_posted", "fieldtype": "Check", "width": 100}
	]

	date_filter = filters.get("posting_date") or today()

	data = frappe.db.sql("""
		SELECT
			po.payment_ref,
			po.from_account,
			po.amount,
			po.payment_rail,
			po.status,
			po.utr_number,
			po.settled_at,
			CASE WHEN btl.name IS NOT NULL THEN 1 ELSE 0 END as ledger_posted
		FROM `tabBanking Payment Order` po
		LEFT JOIN `tabBanking Transaction Ledger` btl 
			ON btl.source_docname = po.name 
			AND btl.source_doctype = 'Banking Payment Order'
		WHERE DATE(po.creation) = %s
		ORDER BY po.creation DESC
	""", date_filter, as_dict=True)

	return columns, data
