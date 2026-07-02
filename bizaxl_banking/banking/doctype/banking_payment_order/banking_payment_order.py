# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, now_datetime


class BankingPaymentOrder(Document):
	"""Controller for Banking Payment Order with Maker-Checker workflow."""

	def autoname(self):
		"""Auto-generate payment reference: PAY-YYYYMM-XXXXX."""
		from frappe.model.naming import make_autoname
		prefix = f"PAY-{frappe.utils.nowdate()[:7].replace('-', '')}-"
		self.name = make_autoname(prefix + "#####")

	def validate(self):
		self.validate_maker_checker()
		self.validate_balance()
		self.validate_payment_rail_limits()

	def validate_maker_checker(self):
		"""Ensure Maker and Checker are different users."""
		if self.maker and self.checker and self.maker == self.checker:
			frappe.throw("Maker and Checker cannot be the same user.")

	def validate_balance(self):
		"""Ensure sufficient balance for the payment."""
		if self.from_account and self.amount:
			account = frappe.get_doc("Banking Account", self.from_account)
			if account.current_balance < self.amount:
				frappe.throw(
					f"Insufficient balance in account {self.from_account}. "
					f"Current balance: {account.current_balance}, Required: {self.amount}"
				)

	def validate_payment_rail_limits(self):
		"""Validate payment rail limits (Indian banking typical limits)."""
		if self.payment_rail == "RTGS" and self.amount < 200000:
			frappe.throw("RTGS requires minimum amount of ₹2,00,000.")
		if self.payment_rail == "NEFT" and self.amount > 5000000:
			frappe.throw("NEFT transaction exceeds typical limit of ₹50,00,000.")
		if self.payment_rail == "UPI" and self.amount > 100000:
			frappe.throw("UPI transaction exceeds limit of ₹1,00,000.")

	def on_submit(self):
		"""Process payment on submit."""
		self.process_payment()

	def process_payment(self):
		"""Process the payment: debit from account, create transaction record."""
		if self.status not in ("Submitted", "Settled"):
			return

		# Debit from account
		account = frappe.get_doc("Banking Account", self.from_account)
		ledger = account.update_balance(
			debit=self.amount,
			transaction_type="Debit",
			reference_doctype="Banking Payment Order",
			reference_docname=self.name
		)

		# Generate UTR number
		self.utr_number = f"UTR{now_datetime().strftime('%Y%m%d%H%M%S')}{frappe.generate_hash(length=6)}"
		self.status = "Settled"
		self.settled_at = now_datetime()
		self.db_set("utr_number", self.utr_number)
		self.db_set("status", "Settled")
		self.db_set("settled_at", self.settled_at)

		# Log transaction
		frappe.db.commit()
		frappe.msgprint(f"Payment processed successfully. UTR: {self.utr_number}")

	def on_cancel(self):
		"""Reverse payment on cancel."""
		if self.status == "Settled":
			account = frappe.get_doc("Banking Account", self.from_account)
			account.update_balance(
				credit=self.amount,
				transaction_type="Reversal",
				reference_doctype="Banking Payment Order",
				reference_docname=self.name
			)

	def before_submit(self):
		"""Before submit - ensure all required fields are present."""
		if not self.checker:
			frappe.throw("Checker is required before submission.")
