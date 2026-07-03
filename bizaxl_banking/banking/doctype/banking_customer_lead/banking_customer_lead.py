# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class BankingCustomerLead(Document):
	"""CRM Lead — tracks prospect from inquiry through KYC to account opening."""
	
	def autoname(self):
		from frappe.model.naming import make_autoname
		prefix = f"LEAD-{frappe.utils.nowdate()[:7]}-"
		self.name = make_autoname(prefix + ".#####")

	def validate(self):
		self.validate_mobile()
		self.set_defaults()

	def validate_mobile(self):
		"""Validate Indian mobile number."""
		if self.mobile:
			import re
			mobile = self.mobile.strip()
			if not re.match(r"^[6-9]\d{9}$", mobile):
				frappe.throw("Invalid Mobile Number. Must be a 10-digit Indian mobile number.")

	def set_defaults(self):
		"""Set default values."""
		if not self.lead_status:
			self.lead_status = "New"
		if not self.lead_date:
			self.lead_date = today()

	def before_save(self):
		"""Auto-assign lead to RM if not assigned."""
		if not self.assigned_rm and self.branch:
			rms = frappe.get_all(
				"Banking Customer",
				filters={"branch": self.branch, "relationship_manager": ("is", "set")},
				fields=["relationship_manager"],
				limit=1
			)
			if rms:
				self.assigned_rm = rms[0].relationship_manager

	@frappe.whitelist()
	def convert_to_customer(self):
		"""Convert lead to a Banking Customer record."""
		if self.lead_status not in ("Qualified", "Converted"):
			frappe.throw(f"Cannot convert lead with status '{self.lead_status}'. Status must be 'Qualified'.")

		customer = frappe.get_doc({
			"doctype": "Banking Customer",
			"customer_type": self.customer_type or "Individual",
			"full_name": self.full_name,
			"date_of_birth": self.date_of_birth or today(),
			"pan_number": self.pan_number,
			"aadhaar_masked": self.aadhaar_masked,
			"mobile": self.mobile,
			"kyc_status": "Pending",
			"risk_category": "Low",
			"fatca_status": "Exempt",
			"branch": self.branch,
			"relationship_manager": self.assigned_rm
		})
		customer.insert(ignore_permissions=True)

		self.lead_status = "Converted"
		self.converted_to_customer = customer.name
		self.db_set("lead_status", "Converted")
		self.db_set("converted_to_customer", customer.name)

		frappe.msgprint(f"Lead {self.name} converted to Customer {customer.name}")
		return customer.name
