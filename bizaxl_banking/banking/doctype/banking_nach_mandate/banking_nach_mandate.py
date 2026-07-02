# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingNachMandate(Document):
	"""Controller for Banking NACH Mandate with status tracking."""
	
	def validate(self):
		self.validate_amount()

	def validate_amount(self):
		"""Ensure max amount is positive."""
		if self.max_amount <= 0:
			frappe.throw("Max Amount must be greater than zero.")
