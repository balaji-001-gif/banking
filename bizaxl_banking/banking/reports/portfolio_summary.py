# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


def execute(filters=None):
	columns = [
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Banking Branch", "width": 150},
		{"label": "Total Accounts", "fieldname": "total_accounts", "fieldtype": "Int", "width": 120},
		{"label": "Total Deposits (₹)", "fieldname": "total_deposits", "fieldtype": "Currency", "width": 150},
		{"label": "Total Advances (₹)", "fieldname": "total_advances", "fieldtype": "Currency", "width": 150},
		{"label": "NPA Amount (₹)", "fieldname": "npa_amount", "fieldtype": "Currency", "width": 150},
		{"label": "NPA %", "fieldname": "npa_pct", "fieldtype": "Percent", "width": 100},
		{"label": "CD Ratio %", "fieldname": "cd_ratio", "fieldtype": "Percent", "width": 100}
	]

	data = frappe.db.sql("""
		SELECT
			ba.branch,
			COUNT(DISTINCT ba.name) as total_accounts,
			COALESCE(SUM(ba.current_balance), 0) as total_deposits,
			COALESCE(SUM(la.sanctioned_amount), 0) as total_advances,
			COALESCE(SUM(CASE WHEN npa.npa_classification IN ('Sub-standard', 'Doubtful', 'Loss') THEN la.outstanding_principal ELSE 0 END), 0) as npa_amount
		FROM `tabBanking Account` ba
		LEFT JOIN `tabBanking Loan Account` la ON la.name IN (
			SELECT name FROM `tabBanking Loan Account` WHERE loan_application IN (
				SELECT name FROM `tabBanking Loan Application` WHERE applicant IN (
					SELECT name FROM `tabBanking Customer` WHERE branch = ba.branch
				)
			)
		)
		LEFT JOIN `tabBanking NPA Tracker` npa ON npa.loan_account = la.name
		GROUP BY ba.branch
	""", as_dict=True)

	for row in data:
		if row.total_advances > 0:
			row.npa_pct = round(row.npa_amount / row.total_advances * 100, 2)
			row.cd_ratio = round(row.total_advances / row.total_deposits * 100, 2) if row.total_deposits > 0 else 0
		else:
			row.npa_pct = 0
			row.cd_ratio = 0

	return columns, data
