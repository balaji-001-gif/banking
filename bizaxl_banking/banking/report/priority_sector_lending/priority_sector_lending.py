# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
		{"label": "Sector", "fieldname": "sector", "fieldtype": "Data", "width": 180},
		{"label": "Target (%)", "fieldname": "target_pct", "fieldtype": "Percent", "width": 80},
		{"label": "Total Advances (₹)", "fieldname": "total_advances", "fieldtype": "Currency", "width": 180},
		{"label": "PSL Achievement (₹)", "fieldname": "psl_achievement", "fieldtype": "Currency", "width": 180},
		{"label": "Achievement (%)", "fieldname": "achievement_pct", "fieldtype": "Percent", "width": 120},
		{"label": "Shortfall (₹)", "fieldname": "shortfall", "fieldtype": "Currency", "width": 180}
	]

	sectors = [
		{"sector": "Agriculture", "target_pct": 18.0},
		{"sector": "MSME", "target_pct": 15.0},
		{"sector": "Weaker Section", "target_pct": 10.0},
		{"sector": "Education", "target_pct": 5.0},
		{"sector": "Housing", "target_pct": 5.0}
	]

	# Get total advances
	total_advances_result = frappe.db.sql("""
		SELECT COALESCE(SUM(sanctioned_amount), 0) as total
		FROM `tabBanking Loan Account`
		WHERE account_status IN ('Active', 'NPA')
	""", as_dict=True)
	total_advances = total_advances_result[0].total

	data = []
	for sector in sectors:
		# Get PSL advances (based on loan product mapping)
		product_map = {
			"Agriculture": "Agri",
			"MSME": "MSME",
			"Weaker Section": "Microfinance",
			"Education": "Personal",
			"Housing": "Home"
		}
		loan_product = product_map.get(sector["sector"], "")

		psl_result = frappe.db.sql("""
			SELECT COALESCE(SUM(bla.sanctioned_amount), 0) as psl_total
			FROM `tabBanking Loan Account` bla
			JOIN `tabBanking Loan Application` blapp ON blapp.name = bla.loan_application
			WHERE bla.account_status IN ('Active', 'NPA')
				AND blapp.loan_product = %s
		""", loan_product, as_dict=True)

		psl_achievement = psl_result[0].psl_total
		target_amount = round(total_advances * sector["target_pct"] / 100, 2)
		achievement_pct = round(psl_achievement / total_advances * 100, 2) if total_advances > 0 else 0
		shortfall = max(0, target_amount - psl_achievement)

		data.append({
			"sector": sector["sector"],
			"target_pct": sector["target_pct"],
			"total_advances": total_advances,
			"psl_achievement": psl_achievement,
			"achievement_pct": achievement_pct,
			"shortfall": shortfall
		})

	return columns, data
