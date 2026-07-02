# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingBranch(Document):
	"""Controller for Banking Branch with IFSC and branch code validation."""

	def validate(self):
		self.validate_ifsc()
		self.validate_branch_code()

	def validate_ifsc(self):
		"""Validate IFSC format: 4 letters, 0, 6 alphanumeric."""
		if self.ifsc_code:
			import re
			if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", self.ifsc_code.upper()):
				frappe.throw("Invalid IFSC Code format. Must be 11 characters (e.g., HDFC0001234).")

	def validate_branch_code(self):
		"""Ensure branch code is set."""
		if not self.branch_code:
			frappe.throw("Branch Code is required.")
