# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, add_days


def execute(filters=None):
	columns = [
		{"label": "Loan Account", "fieldname": "loan_account_no", "fieldtype": "Data", "width": 160},
		{"label": "Customer", "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
		{"label": "EMI Amount (₹)", "fieldname": "emi_amount", "fieldtype": "Currency", "width": 120},
		{"label": "EMI Date", "fieldname": "emi_date", "fieldtype": "Int", "width": 80},
		{"label": "Outstanding (₹)", "fieldname": "outstanding_principal", "fieldtype": "Currency", "width": 150},
		{"label": "NACH Linked", "fieldname": "linked_mandate", "fieldtype": "Link", "options": "Banking NACH Mandate", "width": 160},
		{"label": "Status", "fieldname": "account_status", "fieldtype": "Data", "width": 100}
	]

	next_7_days = add_days(today(), 7)

	data = frappe.db.sql("""
		SELECT
			bla.loan_account_no,
			(SELECT bc.full_name FROM `tabBanking Customer` bc
			 WHERE bc.name = (SELECT applicant FROM `tabBanking Loan Application` bla2
							  WHERE bla2.name = bla.loan_application)) as customer_name,
			bla.emi_amount,
			bla.emi_date,
			bla.outstanding_principal,
			bla.linked_mandate,
			bla.account_status
		FROM `tabBanking Loan Account` bla
		WHERE bla.account_status IN ('Active', 'NPA')
			AND bla.emi_date >= DAY(CURDATE())
			AND bla.emi_date <= DAY(%s)
		ORDER BY bla.emi_date
	""", next_7_days, as_dict=True)

	return columns, data
