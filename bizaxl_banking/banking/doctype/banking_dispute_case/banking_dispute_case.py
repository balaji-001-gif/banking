# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime


class BankingDisputeCase(Document):
	"""Controller for Banking Dispute Case with SLA tracking and auto-reversal."""

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

	def on_update(self):
		"""Auto-trigger reversal when dispute is resolved with Reversal action."""
		if self.has_value_changed("status") and self.status == "Resolved - Upheld" and self.resolution_action == "Reversal":
			self.auto_reverse_transaction()

	def auto_reverse_transaction(self):
		"""Auto-reverse the linked payment transaction."""
		if not self.linked_transaction:
			return

		payment = frappe.get_doc("Banking Payment Order", self.linked_transaction)
		if payment.docstatus == 1:
			account = frappe.get_doc("Banking Account", payment.from_account)
			new_balance = account.current_balance + payment.amount

			# Create reversal transaction ledger entry (insert only - don't submit to avoid double balance update)
			ledger = frappe.get_doc({
				"doctype": "Banking Transaction Ledger",
				"posting_date": frappe.utils.today(),
				"value_date": frappe.utils.today(),
				"account": payment.from_account,
				"debit_amount": 0,
				"credit_amount": payment.amount,
				"running_balance": new_balance,
				"source_doctype": "Banking Dispute Case",
				"source_docname": self.name,
				"transaction_type": "Reversal",
				"is_reversed": 1
			})
			ledger.insert(ignore_permissions=True)

			# Restore account balance directly (avoid on_submit double-counting)
			account.db_set("current_balance", new_balance)
			account.db_set("available_balance", new_balance)

			# Cancel the payment order
			payment.cancel()

			frappe.msgprint(f"Transaction {self.linked_transaction} has been reversed as part of dispute resolution.")


def auto_escalate_overdue_disputes():
	"""Scheduled function to auto-escalate disputes past their SLA deadline."""
	now = now_datetime()
	overdue_disputes = frappe.get_all(
		"Banking Dispute Case",
		filters={
			"sla_deadline": ("<", now),
			"status": ("in", ["Open", "Under Investigation"])
		}
	)
	for d in overdue_disputes:
		frappe.db.set_value("Banking Dispute Case", d.name, "status", "Escalated")
		frappe.msgprint(f"Dispute {d.name} auto-escalated due to SLA breach.")