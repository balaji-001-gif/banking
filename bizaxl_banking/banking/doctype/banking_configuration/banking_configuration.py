# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingConfiguration(Document):
	"""Controller for Banking Configuration (singleton)."""

	def validate(self):
		self.validate_ifsc_prefix()
		self.validate_aml_threshold()

	def validate_ifsc_prefix(self):
		"""Ensure IFSC prefix is 4 characters."""
		if self.ifsc_prefix and len(self.ifsc_prefix) != 4:
			frappe.throw("IFSC Prefix must be exactly 4 characters (e.g., BAXL).")

	def validate_aml_threshold(self):
		"""Ensure AML threshold is positive."""
		if self.aml_threshold_inr and self.aml_threshold_inr <= 0:
			frappe.throw("AML Threshold must be greater than zero.")
