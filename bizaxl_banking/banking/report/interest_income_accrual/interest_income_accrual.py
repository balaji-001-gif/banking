# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


def execute(filters=None):
	columns = [
		{"label": "Product Type", "fieldname": "product_type", "fieldtype": "Data", "width": 130},
		{"label": "Total Deposits (₹)", "fieldname": "total_deposits", "fieldtype": "Currency", "width": 150},
		{"label": "Avg Interest Rate (%)", "fieldname": "avg_interest_rate", "fieldtype": "Percent", "width": 130},
		{"label": "Monthly Accrued (₹)", "fieldname": "monthly_accrued", "fieldtype": "Currency", "width": 150},
		{"label": "TDS Deducted (₹)", "fieldname": "tds_deducted", "fieldtype": "Currency", "width": 150},
		{"label": "Net Payable (₹)", "fieldname": "net_payable", "fieldtype": "Currency", "width": 150}
	]

	data = frappe.db.sql("""
		SELECT
			bdp.product_type,
			COALESCE(SUM(ba.current_balance), 0) as total_deposits,
			COALESCE(AVG(bdp.interest_rate), 0) as avg_interest_rate
		FROM `tabBanking Deposit Product` bdp
		LEFT JOIN `tabBanking Account` ba ON ba.deposit_product = bdp.name
			AND ba.account_status = 'Active'
		GROUP BY bdp.product_type
	""", as_dict=True)

	for row in data:
		row.monthly_accrued = round(row.total_deposits * row.avg_interest_rate / 100 / 12, 2)
		row.tds_deducted = round(row.monthly_accrued * 0.10, 2) if row.monthly_accrued > 40000 / 12 else 0
		row.net_payable = row.monthly_accrued - row.tds_deducted

	return columns, data
