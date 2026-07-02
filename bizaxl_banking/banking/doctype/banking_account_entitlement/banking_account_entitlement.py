# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingAccountEntitlement(Document):
	"""Multi-user access for business accounts: Owner/Accountant/Auditor levels."""
	
	def validate(self):
		self.validate_entitlement()
		self.validate_unique_user()

	def validate_entitlement(self):
		"""Validate that each entitlement has proper access level."""
		if not self.access_level:
			frappe.throw("Access Level is required.")

	def validate_unique_user(self):
		"""Ensure same user is not added twice for same account."""
		existing = frappe.get_all(
			"Banking Account Entitlement",
			filters={
				"account": self.account,
				"user": self.user,
				"name": ("!=", self.name)
			}
		)
		if existing:
			frappe.throw(f"User {self.user} already has entitlement on account {self.account}.")
