# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
		{"label": "Loan Account", "fieldname": "loan_account", "fieldtype": "Link", "options": "Banking Loan Account", "width": 160},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Banking Customer", "width": 160},
		{"label": "NPA Classification", "fieldname": "npa_classification", "fieldtype": "Data", "width": 130},
		{"label": "Days Past Due", "fieldname": "days_past_due", "fieldtype": "Int", "width": 100},
		{"label": "Overdue Amount (₹)", "fieldname": "overdue_amount", "fieldtype": "Currency", "width": 150},
		{"label": "Outstanding (₹)", "fieldname": "outstanding_principal", "fieldtype": "Currency", "width": 150},
		{"label": "Provision (₹)", "fieldname": "provision_amount", "fieldtype": "Currency", "width": 150},
		{"label": "Recovery Stage", "fieldname": "recovery_stage", "fieldtype": "Data", "width": 120}
	]

	classification_filter = filters.get("npa_classification")

	conditions = "WHERE bnt.npa_classification != 'SMA-0'"
	params = []

	if classification_filter:
		conditions += " AND bnt.npa_classification = %s"
		params.append(classification_filter)

	data = frappe.db.sql(f"""
		SELECT
			bnt.loan_account,
			bla.loan_application,
			(SELECT bc.full_name FROM `tabBanking Customer` bc 
			 WHERE bc.name = (SELECT applicant FROM `tabBanking Loan Application` bla2 
							  WHERE bla2.name = bla.loan_application)) as customer,
			bnt.npa_classification,
			bnt.days_past_due,
			bnt.overdue_amount,
			bla.outstanding_principal,
			bnt.provision_amount,
			bnt.recovery_stage
		FROM `tabBanking NPA Tracker` bnt
		JOIN `tabBanking Loan Account` bla ON bla.name = bnt.loan_account
		{conditions}
		ORDER BY bnt.days_past_due DESC
	""", params, as_dict=True)

	return columns, data
