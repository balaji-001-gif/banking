# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, date_diff, getdate


def execute(filters=None):
	columns = [
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Banking Customer", "width": 180},
		{"label": "Full Name", "fieldname": "full_name", "fieldtype": "Data", "width": 180},
		{"label": "KYC Status", "fieldname": "kyc_status", "fieldtype": "Data", "width": 120},
		{"label": "Risk Category", "fieldname": "risk_category", "fieldtype": "Data", "width": 100},
		{"label": "Days Since Pending", "fieldname": "days_pending", "fieldtype": "Int", "width": 120},
		{"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Banking Branch", "width": 150},
		{"label": "RM", "fieldname": "relationship_manager", "fieldtype": "Link", "options": "User", "width": 150}
	]

	branch_filter = filters.get("branch")

	conditions = "WHERE bc.kyc_status IN ('Pending', 'Rejected', 'Re-KYC Due')"
	params = []

	if branch_filter:
		conditions += " AND bc.branch = %s"
		params.append(branch_filter)

	data = frappe.db.sql(f"""
		SELECT
			bc.name as customer,
			bc.full_name,
			bc.kyc_status,
			bc.risk_category,
			DATEDIFF(CURDATE(), bc.modified) as days_pending,
			bc.branch,
			bc.relationship_manager
		FROM `tabBanking Customer` bc
		{conditions}
		ORDER BY days_pending DESC
	""", params, as_dict=True)

	return columns, data
