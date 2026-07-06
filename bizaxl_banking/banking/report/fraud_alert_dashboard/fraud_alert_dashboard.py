# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


def execute(filters=None):
	columns = [
		{"label": "Alert ID", "fieldname": "name", "fieldtype": "Link", "options": "Banking Fraud Alert", "width": 160},
		{"label": "Alert Type", "fieldname": "alert_type", "fieldtype": "Data", "width": 150},
		{"label": "Triggered On", "fieldname": "triggered_on", "fieldtype": "Datetime", "width": 160},
		{"label": "Account", "fieldname": "account", "fieldtype": "Link", "options": "Banking Account", "width": 150},
		{"label": "Risk Score", "fieldname": "risk_score", "fieldtype": "Int", "width": 80},
		{"label": "Auto-Hold", "fieldname": "auto_hold_applied", "fieldtype": "Check", "width": 80},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": "SLA Breach (hrs)", "fieldname": "hours_open", "fieldtype": "Float", "width": 120}
	]

	status_filter = filters.get("status")
	type_filter = filters.get("alert_type")

	conditions = "WHERE 1=1"
	params = []

	if status_filter:
		conditions += " AND bfa.status = %s"
		params.append(status_filter)
	if type_filter:
		conditions += " AND bfa.alert_type = %s"
		params.append(type_filter)

	data = frappe.db.sql(f"""
		SELECT
			bfa.name,
			bfa.alert_type,
			bfa.triggered_on,
			bfa.account,
			bfa.risk_score,
			bfa.auto_hold_applied,
			bfa.status,
			TIMESTAMPDIFF(HOUR, bfa.triggered_on, NOW()) as hours_open,
			bfa.investigated_by
		FROM `tabBanking Fraud Alert` bfa
		{conditions}
		ORDER BY bfa.risk_score DESC, bfa.triggered_on DESC
	""", params, as_dict=True)

	return columns, data
