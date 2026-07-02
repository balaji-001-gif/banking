# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, getdate
import json


def execute(filters=None):
	columns = [
		{"label": "Report Type", "fieldname": "report_type", "fieldtype": "Data", "width": 100},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Banking Customer", "width": 180},
		{"label": "Account", "fieldname": "account", "fieldtype": "Link", "options": "Banking Account", "width": 150},
		{"label": "Transaction Ref", "fieldname": "txn_ref", "fieldtype": "Data", "width": 160},
		{"label": "Amount (₹)", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
		{"label": "Transaction Date", "fieldname": "txn_date", "fieldtype": "Date", "width": 120},
		{"label": "Narration", "fieldname": "narration", "fieldtype": "Data", "width": 200}
	]

	from_date = filters.get("from_date") or getdate(today()).replace(day=1)
	to_date = filters.get("to_date") or today()

	ctr_data = frappe.db.sql("""
		SELECT
			'CTR' as report_type,
			ba.customer,
			po.from_account as account,
			po.payment_ref as txn_ref,
			po.amount,
			DATE(po.creation) as txn_date,
			po.narration
		FROM `tabBanking Payment Order` po
		JOIN `tabBanking Account` ba ON ba.name = po.from_account
		WHERE po.status = 'Settled'
			AND po.amount >= 1000000
			AND DATE(po.creation) BETWEEN %s AND %s
	""", (from_date, to_date), as_dict=True)

	str_data = frappe.db.sql("""
		SELECT
			'STR' as report_type,
			ba.customer,
			bfa.account,
			bfa.name as txn_ref,
			bfa.risk_score as amount,
			DATE(bfa.triggered_on) as txn_date,
			bfa.status as narration
		FROM `tabBanking Fraud Alert` bfa
		JOIN `tabBanking Account` ba ON ba.name = bfa.account
		WHERE bfa.status IN ('Confirmed Fraud', 'Under Review')
			AND DATE(bfa.triggered_on) BETWEEN %s AND %s
	""", (from_date, to_date), as_dict=True)

	data = ctr_data + str_data
	data.sort(key=lambda x: x["txn_date"], reverse=True)

	return columns, data


@frappe.whitelist()
def generate_fiu_xml(from_date=None, to_date=None):
	"""Generate FIU-IND prescribed XML for CTR/STR submission."""
	from frappe.utils import getdate, today
	
	if not from_date:
		from_date = str(getdate(today()).replace(day=1))
	if not to_date:
		to_date = today()

	ctrs = frappe.db.sql("""
		SELECT
			ba.customer,
			bc.full_name,
			bc.pan_number,
			po.from_account,
			po.amount,
			po.utr_number,
			po.creation,
			po.payment_rail
		FROM `tabBanking Payment Order` po
		JOIN `tabBanking Account` ba ON ba.name = po.from_account
		JOIN `tabBanking Customer` bc ON bc.name = ba.customer
		WHERE po.status = 'Settled'
			AND po.amount >= 1000000
			AND DATE(po.creation) BETWEEN %s AND %s
	""", (from_date, to_date), as_dict=True)

	# Generate a simple JSON report (can be extended to actual XML)
	report = {
		"report_type": "CTR",
		"entity": "Bizaxl Banking",
		"period": {"from": from_date, "to": to_date},
		"transactions": []
	}

	for ctr in ctrs:
		report["transactions"].append({
			"customer_name": ctr.full_name,
			"pan": ctr.pan_number,
			"account": ctr.from_account,
			"amount": ctr.amount,
			"utr": ctr.utr_number,
			"date": str(ctr.creation),
			"channel": ctr.payment_rail
		})

	return report
