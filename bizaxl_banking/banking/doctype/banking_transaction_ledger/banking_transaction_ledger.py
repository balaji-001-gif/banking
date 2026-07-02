# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, now_datetime


class BankingTransactionLedger(Document):
	"""Controller for Banking Transaction Ledger with balance auto-update."""

	def validate(self):
		self.validate_amounts()
		self.validate_running_balance()

	def validate_amounts(self):
		"""Ensure either debit or credit is specified."""
		if not self.debit_amount and not self.credit_amount:
			frappe.throw("Either Debit Amount or Credit Amount must be specified.")
		if self.debit_amount and self.credit_amount:
			frappe.throw("Cannot have both Debit and Credit amounts in a single entry.")

	def validate_running_balance(self):
		"""Calculate running balance if not provided."""
		if not self.running_balance and self.account:
			last_entry = frappe.get_all(
				"Banking Transaction Ledger",
				filters={"account": self.account},
				fields=["running_balance"],
				order_by="creation desc",
				limit=1
			)
			last_balance = last_entry[0].running_balance if last_entry else 0
			self.running_balance = last_balance + (self.credit_amount or 0) - (self.debit_amount or 0)

	def on_submit(self):
		"""Update account balance on submission."""
		if not self.account:
			return
		account = frappe.get_doc("Banking Account", self.account)
		account.db_set("current_balance", self.running_balance)
		account.db_set("available_balance", self.running_balance)
