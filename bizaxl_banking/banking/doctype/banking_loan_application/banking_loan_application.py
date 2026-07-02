# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, add_months


class BankingLoanApplication(Document):
	"""Controller for Banking Loan Application with co-applicants and risk assessment."""

	def validate(self):
		self.validate_amount()
		self.validate_foir()
		self.validate_bureau_score()
		self.auto_risk_grade()

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

	def on_submit(self):
		"""On approval, automatically create a Loan Account."""
		if self.decision == "Approved":
			self.create_loan_account()

	def create_loan_account(self):
		"""Create a Loan Account from approved application."""
		loan_account_no = f"LOAN-{frappe.utils.nowdate()[:7].replace('-', '')}-{frappe.generate_hash(length=5)}"

		# Calculate EMI (simple flat rate for now)
		annual_rate = 12.0  # Default 12% if not configured
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
			"interest_rate": 12.0,
			"rate_type": "Floating (MCLR-linked)",
			"emi_amount": emi,
			"emi_date": 5,  # 5th of every month
			"account_status": "Active"
		})
		loan_account.insert(ignore_permissions=True)
		frappe.msgprint(f"Loan Account {loan_account_no} created successfully.")
