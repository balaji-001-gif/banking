# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
		{"label": "Classification", "fieldname": "npa_classification", "fieldtype": "Data", "width": 150},
		{"label": "No. of Accounts", "fieldname": "count", "fieldtype": "Int", "width": 130},
		{"label": "Total Outstanding (₹)", "fieldname": "total_outstanding", "fieldtype": "Currency", "width": 180},
		{"label": "Total Overdue (₹)", "fieldname": "total_overdue", "fieldtype": "Currency", "width": 180},
		{"label": "Provision Required (₹)", "fieldname": "provision_required", "fieldtype": "Currency", "width": 180},
		{"label": "Provision Held (₹)", "fieldname": "provision_held", "fieldtype": "Currency", "width": 180}
	]

	# RBI provisioning norms
	provision_rates = {
		"SMA-0": 0.0025,
		"SMA-1": 0.10,
		"SMA-2": 0.25,
		"Sub-standard": 0.15,
		"Doubtful": 0.50,
		"Loss": 1.00
	}

	data = frappe.db.sql("""
		SELECT
			npa_classification,
			COUNT(*) as count,
			COALESCE(SUM(bla.outstanding_principal), 0) as total_outstanding,
			COALESCE(SUM(overdue_amount), 0) as total_overdue,
			COALESCE(SUM(provision_amount), 0) as provision_held
		FROM `tabBanking NPA Tracker` bnt
		JOIN `tabBanking Loan Account` bla ON bla.name = bnt.loan_account
		GROUP BY npa_classification
		ORDER BY FIELD(npa_classification, 'SMA-0', 'SMA-1', 'SMA-2', 'Sub-standard', 'Doubtful', 'Loss')
	""", as_dict=True)

	for row in data:
		rate = provision_rates.get(row.npa_classification, 0.0025)
		row.provision_required = round(row.total_outstanding * rate, 2)

	return columns, data
