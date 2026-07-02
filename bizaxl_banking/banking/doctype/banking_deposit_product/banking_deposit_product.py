# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingDepositProduct(Document):
	"""Controller for Banking Deposit Product with validation."""

	def validate(self):
		self.validate_interest_rate()
		self.validate_tenure()

	def validate_interest_rate(self):
		"""Ensure interest rate is within reasonable range."""
		if self.interest_rate:
			if self.interest_rate < 0:
				frappe.throw("Interest Rate cannot be negative.")
			if self.interest_rate > 25:
				frappe.throw("Interest Rate exceeds maximum allowed limit of 25%.")

	def validate_tenure(self):
		"""Ensure min tenure doesn't exceed max tenure."""
		if self.min_tenure_days and self.max_tenure_days and self.min_tenure_days > self.max_tenure_days:
			frappe.throw("Minimum Tenure cannot exceed Maximum Tenure.")
