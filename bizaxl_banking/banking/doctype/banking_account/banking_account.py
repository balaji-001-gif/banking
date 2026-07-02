# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, add_months, getdate, date_diff


class BankingAccount(Document):
	"""Controller for Banking Account with balance management, joint holders,
	dormant classification, and closure validation."""

	def autoname(self):
		"""Auto-generate account number: ACC-YYYYMM-XXXXX."""
		from frappe.model.naming import make_autoname
		prefix = f"ACC-{frappe.utils.nowdate()[:7].replace('-', '')}-"
		self.name = make_autoname(prefix + "#####")

	def validate(self):
		self.validate_balances()
		self.validate_opening()
		self.validate_closure()

	def validate_balances(self):
		"""Ensure available_balance never exceeds current_balance."""
		if self.available_balance > self.current_balance:
			frappe.throw("Available Balance cannot exceed Current Balance.")

	def validate_opening(self):
		"""Ensure date_opened is set."""
		if not self.date_opened:
			self.date_opened = today()

	def validate_closure(self):
		"""Validate account closure requirements.
		
		When closing an account:
		- Balance must be zero
		- No active standing instructions
		- No active NACH mandates
		- No pending payment orders
		"""
		if self.has_value_changed("account_status") and self.account_status == "Closed":
			# Check balance is zero
			if self.current_balance != 0:
				frappe.throw(
					f"Cannot close account {self.name}. Current balance is ₹{self.current_balance}. "
					f"Please transfer/withdraw all funds before closing."
				)

			# Check no active standing instructions
			active_instructions = frappe.get_all(
				"Banking Standing Instruction",
				filters={
					"from_account": self.name,
					"status": "Active"
				}
			)
			if active_instructions:
				frappe.throw(
					f"Cannot close account {self.name}. There are {len(active_instructions)} "
					f"active standing instruction(s). Please cancel them first."
				)

			# Check no active NACH mandates
			active_mandates = frappe.get_all(
				"Banking NACH Mandate",
				filters={
					"account": self.name,
					"status": ("in", ["Pending Registration", "Active"])
				}
			)
			if active_mandates:
				frappe.throw(
					f"Cannot close account {self.name}. There are {len(active_mandates)} "
					f"active NACH mandate(s). Please cancel them first."
				)

			# Check no pending payment orders
			pending_payments = frappe.get_all(
				"Banking Payment Order",
				filters={
					"from_account": self.name,
					"status": ("in", ["Draft", "Pending Approval", "Approved"])
				}
			)
			if pending_payments:
				frappe.throw(
					f"Cannot close account {self.name}. There are {len(pending_payments)} "
					f"pending payment order(s). Please clear them first."
				)

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


def auto_classify_dormant_accounts():
	"""Scheduled function to classify accounts as dormant.
	
	An account is considered dormant if:
	- No transaction in the last 12 months
	- Current status is Active
	"""
	twelve_months_ago = add_months(getdate(today()), -12)
	
	dormant_accounts = frappe.db.sql("""
		SELECT ba.name
		FROM `tabBanking Account` ba
		WHERE ba.account_status = 'Active'
			AND ba.modified <= %s
			AND NOT EXISTS (
				SELECT 1 FROM `tabBanking Transaction Ledger` btl
				WHERE btl.account = ba.name
					AND btl.creation >= %s
			)
	""", (twelve_months_ago, twelve_months_ago), as_dict=True)

	for acc in dormant_accounts:
		frappe.db.set_value("Banking Account", acc.name, "account_status", "Dormant")
		frappe.msgprint(f"Account {acc.name} has been classified as Dormant due to 12 months of inactivity.")
