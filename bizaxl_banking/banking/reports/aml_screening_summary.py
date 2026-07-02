# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
		{"label": "Screening Type", "fieldname": "screening_type", "fieldtype": "Data", "width": 130},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Banking Customer", "width": 180},
		{"label": "Lists Checked", "fieldname": "lists_checked", "fieldtype": "Data", "width": 250},
		{"label": "Match Found", "fieldname": "match_found", "fieldtype": "Check", "width": 100},
		{"label": "Disposition", "fieldname": "disposition", "fieldtype": "Data", "width": 150},
		{"label": "Screened At", "fieldname": "screened_at", "fieldtype": "Datetime", "width": 160}
	]

	data = frappe.db.sql("""
		SELECT
			screening_type,
			customer,
			lists_checked,
			match_found,
			disposition,
			screened_at
		FROM `tabBanking AML Screening Log`
		ORDER BY screened_at DESC
	""", as_dict=True)

	return columns, data
