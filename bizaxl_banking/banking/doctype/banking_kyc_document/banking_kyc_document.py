# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingKycDocument(Document):
	"""Controller for Banking KYC Document with verification tracking."""

	def validate(self):
		self.validate_expiry()
		self.auto_update_customer_status()

	def validate_expiry(self):
		"""Warn if document is expired or expiring soon."""
		if self.expiry_date:
			from frappe.utils import date_diff, getdate, add_days
			days_until_expiry = date_diff(getdate(self.expiry_date), getdate())
			if days_until_expiry < 0:
				frappe.msgprint(f"Warning: Document {self.document_type} (No. {self.document_number}) has already expired.")
			elif days_until_expiry <= 30:
				frappe.msgprint(f"Warning: Document {self.document_type} (No. {self.document_number}) is expiring in {days_until_expiry} days.")

	def auto_update_customer_status(self):
		"""Auto-update customer KYC status on document verification."""
		if self.verification_status == "Verified" and self.customer:
			customer = frappe.get_doc("Banking Customer", self.customer)
			if customer.kyc_status != "Verified":
				customer.db_set("kyc_status", "Verified")
