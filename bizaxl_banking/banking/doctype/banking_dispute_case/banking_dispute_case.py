# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingDisputeCase(Document):
	"""Controller for Banking Dispute Case with SLA tracking."""

	def validate(self):
		self.validate_sla()
		self.validate_resolution()

	def validate_sla(self):
		"""Ensure SLA deadline is after raised on date."""
		if self.raised_on and self.sla_deadline and self.sla_deadline <= self.raised_on:
			frappe.throw("SLA Deadline must be after the date the dispute was raised.")

	def validate_resolution(self):
		"""If status is resolved, resolution action must be set."""
		if "Resolved" in (self.status or "") and not self.resolution_action:
			frappe.throw("Resolution Action is required for resolved disputes.")
