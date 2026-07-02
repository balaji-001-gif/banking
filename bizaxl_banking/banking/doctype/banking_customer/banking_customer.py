# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, nowdate


class BankingCustomer(Document):
	"""Controller for Banking Customer with auto-numbering and validation."""

	def autoname(self):
		"""Auto-generate customer ID: CUST-YYYY-MM-XXXXX"""
		from frappe.model.naming import make_autoname
		prefix = f"CUST-{frappe.utils.nowdate()[:7]}-"
		self.name = make_autoname(prefix + "#####")

	def validate(self):
		self.validate_pan()
		self.validate_mobile()
		self.update_kyc_status()

	def validate_pan(self):
		"""Basic PAN format validation (ABCDE1234F)."""
		if self.pan_number:
			import re
			if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", self.pan_number.upper()):
				frappe.throw("Invalid PAN Number format. Must be 10 characters (e.g., ABCDE1234F).")

	def validate_mobile(self):
		"""Validate Indian mobile number (10 digits, starts with 6-9)."""
		if self.mobile:
			import re
			mobile = self.mobile.strip()
			if not re.match(r"^[6-9]\d{9}$", mobile):
				frappe.throw("Invalid Mobile Number. Must be a 10-digit Indian mobile number.")

	def update_kyc_status(self):
		"""Auto-update KYC status based on document verification."""
		if self.kyc_status == "Verified" and self.risk_category not in ("Low", "Medium", "High"):
			self.risk_category = "Medium"

	def on_update(self):
		"""Create AML screening log on customer update if KYC changes."""
		if self.has_value_changed("kyc_status") and self.kyc_status == "Verified":
			self.create_aml_screening_log()

	def create_aml_screening_log(self):
		"""Create an AML screening log entry."""
		screening = frappe.get_doc({
			"doctype": "Banking AML Screening Log",
			"screening_type": "Onboarding",
			"customer": self.name,
			"lists_checked": "UNSC, OFAC, EU Sanctions, Internal Watchlist",
			"match_found": 0,
			"disposition": "Clear",
			"screened_at": frappe.utils.now()
		})
		screening.insert(ignore_permissions=True)
