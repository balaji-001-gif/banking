# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, date_diff


class BankingStandingInstruction(Document):
	"""Controller for Banking Standing Instruction with auto-execution."""

	def validate(self):
		self.validate_dates()
		self.validate_amount()

	def validate_dates(self):
		"""Ensure start and end dates are valid."""
		if self.start_date and self.end_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw("End Date cannot be before Start Date.")

	def validate_amount(self):
		"""Ensure amount is positive."""
		if self.amount <= 0:
			frappe.throw("Amount must be greater than zero.")

	def execute_instruction(self):
		"""Execute the standing instruction."""
		if self.status != "Active":
			return

		account = frappe.get_doc("Banking Account", self.from_account)
		if account.current_balance < self.amount:
			frappe.log_error(
				f"Insufficient balance for standing instruction {self.name}",
				"Standing Instruction Failed"
			)
			self.status = "Paused"
			self.db_set("status", "Paused")
			return

		# Create transaction ledger entry
		ledger = frappe.get_doc({
			"doctype": "Banking Transaction Ledger",
			"posting_date": today(),
			"value_date": today(),
			"account": self.from_account,
			"debit_amount": self.amount,
			"credit_amount": 0,
			"running_balance": account.current_balance - self.amount,
			"source_doctype": "Banking Standing Instruction",
			"source_docname": self.name,
			"transaction_type": "Debit",
			"is_reversed": 0
		})
		ledger.insert(ignore_permissions=True)

		# Update account balance
		account.db_set("current_balance", account.current_balance - self.amount)
		account.db_set("available_balance", account.available_balance - self.amount)

		# Update last run date
		self.last_run_date = today()
		self.db_set("last_run_date", today())

		# Check if ended
		if self.end_date and getdate(today()) >= getdate(self.end_date):
			self.status = "Completed"
			self.db_set("status", "Completed")


def process_due_instructions():
	"""Scheduled function to process all due standing instructions."""
	today_date = today()
	# OR logic: last_run_date is NULL (never run) OR last_run_date is not today
	instructions = frappe.get_all(
		"Banking Standing Instruction",
		filters=[
			["status", "=", "Active"],
			["start_date", "<=", today_date],
			"or",
			["last_run_date", "is", "not set"],
			["last_run_date", "!=", today_date]
		]
	)

	for inst in instructions:
		doc = frappe.get_doc("Banking Standing Instruction", inst.name)
		doc.execute_instruction()
