# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, now_datetime


class BankingRegulatoryReport(Document):
	"""Controller for Banking Regulatory Report with auto-generation logic."""

	def validate(self):
		self.validate_period()

	def validate_period(self):
		"""Ensure period_from is before period_to."""
		if self.period_from and self.period_to and self.period_from > self.period_to:
			frappe.throw("Period From cannot be after Period To.")

	def generate_report_data(self):
		"""Generate report data based on report type."""
		if self.report_type == "CTR":
			return self.generate_ctr()
		elif self.report_type == "STR":
			return self.generate_str()
		elif self.report_type == "CRILC":
			return self.generate_crilc()
		elif self.report_type == "NPA Return":
			return self.generate_npa_return()
		elif self.report_type == "Priority Sector":
			return self.generate_priority_sector()
		return None

	def generate_ctr(self):
		"""Generate Cash Transaction Report data.
		
		CTR must be filed for cash transactions > ₹10L in a day.
		"""
		ctr_data = frappe.db.sql("""
			SELECT 
				tl.account,
				SUM(tl.debit_amount) as total_debit,
				SUM(tl.credit_amount) as total_credit,
				COUNT(*) as transaction_count,
				DATE(tl.posting_date) as transaction_date
			FROM `tabBanking Transaction Ledger` tl
			WHERE tl.posting_date BETWEEN %s AND %s
				AND tl.transaction_type IN ('Debit', 'Credit')
			GROUP BY tl.account, DATE(tl.posting_date)
			HAVING SUM(tl.debit_amount) > 1000000 OR SUM(tl.credit_amount) > 1000000
		""", (self.period_from, self.period_to), as_dict=True)

		return ctr_data

	def generate_str(self):
		"""Generate Suspicious Transaction Report data."""
		str_data = frappe.db.sql("""
			SELECT 
				fa.account,
				fa.alert_type,
				fa.risk_score,
				fa.status as alert_status,
				fa.triggered_on
			FROM `tabBanking Fraud Alert` fa
			WHERE fa.creation BETWEEN %s AND %s
				AND fa.status IN ('Confirmed Fraud', 'Under Review')
		""", (self.period_from, self.period_to), as_dict=True)

		return str_data

	def generate_crilc(self):
		"""Generate CRILC (Central Repository of Information on Large Credits) data.
		
		All borrowers with aggregate exposure >= ₹5Cr.
		"""
		crilc_data = frappe.db.sql("""
			SELECT 
				la.name as loan_account,
				la.sanctioned_amount,
				la.outstanding_principal,
				la.interest_rate,
				la.account_status,
				nt.npa_classification,
				nt.days_past_due,
				nt.overdue_amount,
				nt.provision_amount
			FROM `tabBanking Loan Account` la
			LEFT JOIN `tabBanking NPA Tracker` nt ON nt.loan_account = la.name
			WHERE la.sanctioned_amount >= 5000000
				AND la.creation BETWEEN %s AND %s
		""", (self.period_from, self.period_to), as_dict=True)

		return crilc_data

	def generate_npa_return(self):
		"""Generate NPA Return data."""
		npa_data = frappe.db.sql("""
			SELECT 
				nt.npa_classification,
				COUNT(*) as account_count,
				SUM(nt.overdue_amount) as total_overdue,
				SUM(nt.provision_amount) as total_provision,
				AVG(nt.days_past_due) as avg_dpd
			FROM `tabBanking NPA Tracker` nt
			WHERE nt.npa_classification IN ('Sub-standard', 'Doubtful', 'Loss')
			GROUP BY nt.npa_classification
		""", as_dict=True)

		return npa_data

	def generate_priority_sector(self):
		"""Generate Priority Sector Lending report."""
		psl_data = frappe.db.sql("""
			SELECT 
				la.interest_rate,
				COUNT(*) as loan_count,
				SUM(la.sanctioned_amount) as total_sanctioned,
				SUM(la.outstanding_principal) as total_outstanding
			FROM `tabBanking Loan Account` la
			JOIN `tabBanking Loan Application` lapp ON lapp.name = la.loan_application
			WHERE lapp.loan_product IN ('Agri', 'Microfinance', 'MSME')
				AND la.creation BETWEEN %s AND %s
			GROUP BY la.interest_rate
		""", (self.period_from, self.period_to), as_dict=True)

		return psl_data

	def generate_and_submit(self):
		"""Generate report data and submit."""
		data = self.generate_report_data()
		if data:
			self.submission_status = "Generated"
			self.db_set("submission_status", "Generated")
			import json
			self.report_file = json.dumps(data, default=str, indent=2)
			frappe.msgprint(f"{self.report_type} report generated successfully with {len(data)} records.")
		else:
			frappe.msgprint(f"No data found for {self.report_type} report in the selected period.")


def generate_scheduled_reports():
	"""Scheduled function to auto-generate regulatory reports weekly.
	
	Generates:
	- NPA Return (quarterly)
	- CTR for large cash transactions
	- Priority Sector report (quarterly)
	"""
	from frappe.utils import add_months, get_first_day, get_last_day, getdate
	
	# Generate NPA Return for current quarter
	today_date = getdate(today())
	
	# Check if any report already generated this period
	existing = frappe.get_all(
		"Banking Regulatory Report",
		filters={
			"report_type": "NPA Return",
			"period_to": today_date,
			"submission_status": ("in", ["Generated", "Submitted", "Acknowledged"])
		}
	)
	if not existing:
		npa_report = frappe.get_doc({
			"doctype": "Banking Regulatory Report",
			"report_type": "NPA Return",
			"period_from": get_first_day(add_months(today_date, -3)),
			"period_to": today_date,
			"submission_status": "Draft"
		})
		npa_report.insert(ignore_permissions=True)
		npa_report.generate_and_submit()

	# Generate Priority Sector report
	psl_existing = frappe.get_all(
		"Banking Regulatory Report",
		filters={
			"report_type": "Priority Sector",
			"period_to": today_date,
			"submission_status": ("in", ["Generated", "Submitted", "Acknowledged"])
		}
	)
	if not psl_existing:
		psl_report = frappe.get_doc({
			"doctype": "Banking Regulatory Report",
			"report_type": "Priority Sector",
			"period_from": get_first_day(add_months(today_date, -3)),
			"period_to": today_date,
			"submission_status": "Draft"
		})
		psl_report.insert(ignore_permissions=True)
		psl_report.generate_and_submit()
