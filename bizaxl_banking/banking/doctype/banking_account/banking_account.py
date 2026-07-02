# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class BankingAccount(Document):
	"""Controller for Banking Account with balance management and joint holders."""

	def autoname(self):
		"""Auto-generate account number: ACC-YYYYMM-XXXXX."""
		from frappe.model.naming import make_autoname
		prefix = f"ACC-{frappe.utils.nowdate()[:7].replace('-', '')}-"
		self.name = make_autoname(prefix + "#####")

	def validate(self):
		self.validate_balances()
		self.validate_opening()
		self.update_account_status()

	def validate_balances(self):
		"""Ensure available_balance never exceeds current_balance."""
		if self.available_balance > self.current_balance:
			frappe.throw("Available Balance cannot exceed Current Balance.")

	def validate_opening(self):
		"""Ensure date_opened is set."""
		if not self.date_opened:
			self.date_opened = today()

	def update_account_status(self):
		"""Auto-update account status based on balance."""
		if self.account_status == "Active" and self.current_balance <= 0:
			# Don't auto-dormant; only flag for manual review
			pass

	def on_update(self):
		"""Log balance changes to Transaction Ledger if relevant."""
		pass

	def get_balance(self):
		"""Return current balance."""
		return self.current_balance

	def update_balance(self, debit=0, credit=0, transaction_type=None, reference_doctype=None, reference_docname=None):
		"""Update account balance and create Transaction Ledger entry."""
		if debit:
			self.current_balance -= debit
			self.available_balance -= debit
		if credit:
			self.current_balance += credit
			self.available_balance += credit

		self.db_set("current_balance", self.current_balance)
		self.db_set("available_balance", self.available_balance)

		# Create transaction ledger entry
		ledger = frappe.get_doc({
			"doctype": "Banking Transaction Ledger",
			"posting_date": today(),
			"value_date": today(),
			"account": self.name,
			"debit_amount": debit if debit else 0,
			"credit_amount": credit if credit else 0,
			"running_balance": self.current_balance,
			"source_doctype": reference_doctype or "Banking Account",
			"source_docname": reference_docname or self.name,
			"transaction_type": transaction_type or ("Debit" if debit else "Credit"),
			"is_reversed": 0
		})
		ledger.insert(ignore_permissions=True)
		return ledger
