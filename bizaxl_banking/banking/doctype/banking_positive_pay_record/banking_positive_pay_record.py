# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate


class BankingPositivePayRecord(Document):
	"""Controller for Positive Pay — customers submit check details in advance.
	
	When a check is presented for payment, the system matches against these
	records. Mismatches trigger a Positive Pay Mismatch fraud alert.
	"""

	def validate(self):
		self.validate_dates()
		self.validate_amount()

	def validate_dates(self):
		"""Ensure cheque date is not in the future."""
		if self.cheque_date and getdate(self.cheque_date) > getdate(today()):
			frappe.throw("Cheque Date cannot be in the future.")

	def validate_amount(self):
		"""Ensure amount is positive."""
		if self.amount <= 0:
			frappe.throw("Cheque amount must be greater than zero.")
