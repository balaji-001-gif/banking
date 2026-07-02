# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class BankingNachMandate(Document):
	"""Controller for Banking NACH Mandate with NPCI integration."""

	def validate(self):
		self.validate_amount()

	def validate_amount(self):
		"""Ensure max amount is positive."""
		if self.max_amount <= 0:
			frappe.throw("Max Amount must be greater than zero.")

	def before_submit(self):
		"""On submit, register mandate with sponsor bank via NPCI."""
		self.register_with_npci()

	def register_with_npci(self):
		"""Register mandate with sponsor bank using NACH NPCI integration.
		
		If NACH integration is enabled and configured, the mandate is
		registered with the sponsor bank. Otherwise, it's registered locally.
		"""
		if self.status != "Pending Registration":
			return

		try:
			from bizaxl_banking.banking.payment_gateways.nach import register_mandate
			result = register_mandate(self)

			if result.get("status") == "registered":
				self.status = "Active"
				self.registered_on = today()
				self.mandate_ref = result.get("sponsor_ref") or result.get("mandate_ref") or self.mandate_ref
				frappe.msgprint(f"NACH Mandate {self.name} registered successfully with sponsor bank.")

			elif result.get("status") == "simulated":
				self.status = "Active"
				self.registered_on = today()
				self.mandate_ref = result.get("mandate_ref") or self.mandate_ref
				frappe.msgprint(f"NACH Mandate {self.name} registered (simulated — no API key).")

			elif result.get("status") == "disabled":
				self.status = "Active"
				self.registered_on = today()
				frappe.msgprint(
					f"NACH Mandate {self.name} registered locally. "
					"Configure NPCI/NACH API keys in Banking Integration Settings for live registration.",
					indicator="yellow"
				)

			else:
				frappe.msgprint(
					f"NACH registration returned: {result.get('message', 'Unknown')}. "
					f"Mandate saved as pending. You can retry after configuring API keys.",
					indicator="orange"
				)

		except Exception as e:
			frappe.log_error(f"NACH registration error for {self.name}: {str(e)}", "NACH Mandate")
			frappe.msgprint(
				"NACH registration service unavailable. Mandate saved as Pending Registration. "
				"Retry after configuring API keys in Banking Integration Settings.",
				indicator="yellow"
			)
