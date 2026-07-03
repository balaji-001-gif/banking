# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, now_datetime


class BankingPaymentOrder(Document):
	"""Controller for Banking Payment Order with Maker-Checker workflow and NPCI integration."""

	def autoname(self):
		"""Auto-generate payment reference: PAY-YYYYMM-XXXXX."""
		from frappe.model.naming import make_autoname
		prefix = f"PAY-{frappe.utils.nowdate()[:7].replace('-', '')}-"
		self.name = make_autoname(prefix + ".#####")

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
		"""Process the payment: debit account + NPCI execution + notification."""
		if self.status not in ("Submitted", "Settled"):
			return

		# Step 1: Execute via NPCI if configured
		from bizaxl_banking.banking.payment_gateways.npci import execute_payment
		npci_result = execute_payment(self)

		if npci_result.get("status") == "failed":
			self.status = "Failed"
			self.db_set("status", "Failed")
			frappe.throw(f"Payment failed: {npci_result.get('error_message', 'NPCI error')}")

		# Step 2: Debit from account
		account = frappe.get_doc("Banking Account", self.from_account)
		account.update_balance(
			debit=self.amount,
			transaction_type="Debit",
			reference_doctype="Banking Payment Order",
			reference_docname=self.name
		)

		# Step 3: Use NPCI UTR or generate local one
		self.utr_number = npci_result.get("utr_number") or f"UTR{now_datetime().strftime('%Y%m%d%H%M%S')}{frappe.generate_hash(length=6)}"
		self.status = "Settled"
		self.settled_at = npci_result.get("settled_at") or now_datetime()
		self.db_set("utr_number", self.utr_number)
		self.db_set("status", "Settled")
		self.db_set("settled_at", self.settled_at)

		# Step 4: Send transaction alert
		try:
			from bizaxl_banking.banking.notifications.messaging import send_transaction_alert
			send_transaction_alert(account.customer, account.name, self)
		except Exception:
			pass  # Non-critical — don't fail payment if notification fails

		status_msg = npci_result.get("message", "")
		frappe.msgprint(f"Payment processed successfully. UTR: {self.utr_number}. {status_msg}")

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
