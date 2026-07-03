# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, add_months


class BankingLoanApplication(Document):
	"""Controller for Banking Loan Application with co-applicants, risk assessment, and bureau integration."""

	def validate(self):
		self.validate_amount()
		self.validate_foir()
		self.validate_bureau_score()
		self.auto_risk_grade()
		self.run_bureau_integration()

	def validate_amount(self):
		"""Ensure requested amount is positive."""
		if self.requested_amount <= 0:
			frappe.throw("Requested Amount must be greater than zero.")

	def validate_foir(self):
		"""Validate FOIR percentage."""
		if self.foir and self.foir > 70:
			frappe.throw("FOIR exceeds maximum allowed limit of 70%.")

	def validate_bureau_score(self):
		"""Validate bureau score range."""
		if self.bureau_score and (self.bureau_score < 300 or self.bureau_score > 900):
			frappe.throw("Bureau Score must be between 300 and 900.")

	def auto_risk_grade(self):
		"""Auto-calculate risk grade based on bureau score and FOIR."""
		if self.bureau_score and not self.internal_risk_grade:
			if self.bureau_score >= 750:
				self.internal_risk_grade = "A1"
			elif self.bureau_score >= 700:
				self.internal_risk_grade = "A2"
			elif self.bureau_score >= 650:
				self.internal_risk_grade = "B1"
			elif self.bureau_score >= 600:
				self.internal_risk_grade = "B2"
			elif self.bureau_score >= 500:
				self.internal_risk_grade = "C"
			else:
				self.internal_risk_grade = "D"

	def run_bureau_integration(self):
		"""Auto-fetch bureau score if PAN is available and bureau is not set.
		
		This runs silently and only populates the score if empty.
		If bureau is enabled, it fetches and updates the score.
		"""
		if self.bureau_score:
			return  # Already has a score

		if not self.applicant:
			return

		pan = frappe.db.get_value("Banking Customer", self.applicant, "pan_number")
		if not pan:
			return

		try:
			from bizaxl_banking.banking.bureau.cibil import fetch_credit_score
			result = fetch_credit_score(pan)
			if result.get("status") in ("success", "simulated"):
				self.bureau_score = result.get("score", 0)
				self.foir = result.get("report", {}).get("credit_utilization", self.foir or 0)
				self.auto_risk_grade()
		except Exception:
			frappe.log_error(f"Bureau fetch failed for application {self.name}", "Bureau Integration")

	def on_submit(self):
		"""On approval, automatically create a Loan Account."""
		if self.decision == "Approved":
			self.create_loan_account()

	def create_loan_account(self):
		"""Create a Loan Account from approved application."""
		from frappe.model.naming import make_autoname
		loan_account_no = make_autoname(
			f"LOAN-{frappe.utils.nowdate()[:7].replace('-', ''):}-" + ".#####"
		)

		# Use rate from application if set, otherwise default to 12%
		annual_rate = frappe.utils.flt(getattr(self, "interest_rate", None)) or 12.0
		monthly_rate = annual_rate / 12 / 100
		tenure_months = self.requested_tenure_months or 60
		emi = round(
			self.requested_amount * monthly_rate * (1 + monthly_rate) ** tenure_months
			/ ((1 + monthly_rate) ** tenure_months - 1)
		) if tenure_months > 0 else 0

		loan_account = frappe.get_doc({
			"doctype": "Banking Loan Account",
			"loan_application": self.name,
			"loan_account_no": loan_account_no,
			"sanctioned_amount": self.requested_amount,
			"outstanding_principal": self.requested_amount,
			"interest_rate": annual_rate,
			"rate_type": "Floating (MCLR-linked)",
			"emi_amount": emi,
			"emi_date": 5,
			"account_status": "Active"
		})
		loan_account.insert(ignore_permissions=True)

		# Try to link NACH mandate for auto-debit
		try:
			self._link_nach_mandate(loan_account, emi)
		except Exception:
			pass

		frappe.msgprint(f"Loan Account {loan_account_no} created successfully.")

	def _link_nach_mandate(self, loan_account, emi_amount):
		"""Try to create a NACH mandate for the loan EMI."""
		customer_accounts = frappe.get_all(
			"Banking Account",
			filters={"customer": self.applicant, "account_status": "Active"},
			limit=1
		)
		if customer_accounts:
			mandate = frappe.get_doc({
				"doctype": "Banking NACH Mandate",
				"account": customer_accounts[0].name,
				"mandate_ref": f"MAN-{loan_account.name}",
				"max_amount": emi_amount,
				"frequency": "Monthly",
				"status": "Pending Registration"
			})
			mandate.insert(ignore_permissions=True)
			loan_account.db_set("linked_mandate", mandate.name)
