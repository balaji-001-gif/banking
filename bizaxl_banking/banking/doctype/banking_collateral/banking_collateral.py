# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingCollateral(Document):
	"""Controller for Banking Collateral with lien management."""

	def validate(self):
		self.validate_values()
		self.validate_lien()

	def validate_values(self):
		"""Ensure market value is positive."""
		if self.market_value <= 0:
			frappe.throw("Market Value must be greater than zero.")

	def validate_lien(self):
		"""Ensure lien amount doesn't exceed market value."""
		if self.lien_amount and self.lien_amount > self.market_value:
			frappe.throw("Lien Amount cannot exceed Market Value.")
