# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, add_months, getdate, date_diff


class BankingLoanAccount(Document):
	"""Controller for Banking Loan Account with EMI, interest, and floating rate management."""

	def validate(self):
		self.validate_amounts()
		self.validate_emi_date()

	def validate_amounts(self):
		"""Ensure amounts are positive."""
		if self.sanctioned_amount <= 0:
			frappe.throw("Sanctioned Amount must be greater than zero.")
		if self.outstanding_principal < 0:
			frappe.throw("Outstanding Principal cannot be negative.")
		if self.interest_rate and self.interest_rate > 50:
			frappe.throw("Interest Rate exceeds maximum allowed limit of 50%.")

	def validate_emi_date(self):
		"""Validate EMI date is between 1 and 28."""
		if self.emi_date and (self.emi_date < 1 or self.emi_date > 28):
			frappe.throw("EMI Date must be between 1 and 28.")

	def calculate_interest(self, days=None):
		"""Calculate interest using daily reducing balance method.
		
		Interest = Outstanding Principal x Rate x Days / 365
		"""
		if not days:
			days = 30
		daily_rate = self.interest_rate / 100 / 365
		interest_amount = round(self.outstanding_principal * daily_rate * days, 2)
		return interest_amount

	def post_interest(self):
		"""Post interest for the current period."""
		interest = self.calculate_interest()
		if interest <= 0:
			return

		account = self._get_customer_account()
		if not account:
			frappe.log_error(f"No account found for loan {self.name}, interest not posted", "Loan Interest Posting")
			return

		ledger = frappe.get_doc({
			"doctype": "Banking Transaction Ledger",
			"posting_date": today(),
			"value_date": today(),
			"account": account,
			"debit_amount": interest,
			"credit_amount": 0,
			"running_balance": self.outstanding_principal + interest,
			"source_doctype": "Banking Loan Account",
			"source_docname": self.name,
			"transaction_type": "Interest",
			"is_reversed": 0
		})
		ledger.insert(ignore_permissions=True)

		self.outstanding_principal += interest
		self.db_set("outstanding_principal", self.outstanding_principal)

	def _get_customer_account(self):
		"""Get the linked customer account for transaction ledger."""
		if self.loan_application:
			customer = frappe.db.get_value("Banking Loan Application", self.loan_application, "applicant")
			if customer:
				accounts = frappe.get_all("Banking Account", filters={"customer": customer}, limit=1)
				if accounts:
					return accounts[0].name
		return None

	def process_emi(self):
		"""Process EMI for this loan account."""
		if self.account_status not in ("Active",):
			return

		if self.emi_amount > self.outstanding_principal:
			emi = self.outstanding_principal
			self.account_status = "Closed"
			self.db_set("account_status", "Closed")
		else:
			emi = self.emi_amount

		account = self._get_customer_account()
		if not account:
			frappe.log_error(f"No account found for loan {self.name}, EMI not processed", "Loan EMI Processing")
			return

		ledger = frappe.get_doc({
			"doctype": "Banking Transaction Ledger",
			"posting_date": today(),
			"value_date": today(),
			"account": account,
			"debit_amount": 0,
			"credit_amount": emi,
			"running_balance": self.outstanding_principal - emi,
			"source_doctype": "Banking Loan Account",
			"source_docname": self.name,
			"transaction_type": "Credit",
			"is_reversed": 0
		})
		ledger.insert(ignore_permissions=True)

		self.outstanding_principal -= emi
		self.db_set("outstanding_principal", self.outstanding_principal)
		self.create_npa_tracker()

	def create_npa_tracker(self):
		"""Create or update NPA tracker entry."""
		trackers = frappe.get_all("Banking NPA Tracker", filters={"loan_account": self.name})
		if trackers:
			return

		tracker = frappe.get_doc({
			"doctype": "Banking NPA Tracker",
			"loan_account": self.name,
			"npa_classification": "SMA-0",
			"days_past_due": 0,
			"overdue_amount": 0,
			"provision_amount": 0
		})
		tracker.insert(ignore_permissions=True)

	def update_interest_rate(self, new_rate):
		"""Update interest rate for floating-rate loans.
		
		This is called when MCLR changes. Only affects loans with 
		rate_type = 'Floating (MCLR-linked)'.
		"""
		if self.rate_type != "Floating (MCLR-linked)":
			frappe.throw(f"Loan {self.name} is not a floating-rate loan. Cannot update rate.")

		if new_rate <= 0 or new_rate > 50:
			frappe.throw("New interest rate must be between 0.01% and 50%.")

		old_rate = self.interest_rate
		self.interest_rate = new_rate
		self.db_set("interest_rate", new_rate)

		# Recalculate EMI based on new rate
		if self.emi_amount > 0 and self.outstanding_principal > 0:
			monthly_rate = new_rate / 12 / 100
			# Estimate remaining tenure based on current EMI
			remaining_tenure_months = max(1, round(self.outstanding_principal / self.emi_amount))
			# Recalculate EMI
			if monthly_rate > 0 and remaining_tenure_months > 0:
				new_emi = round(
					self.outstanding_principal * monthly_rate * (1 + monthly_rate) ** remaining_tenure_months
					/ ((1 + monthly_rate) ** remaining_tenure_months - 1)
				)
				self.emi_amount = new_emi
				self.db_set("emi_amount", new_emi)

		# Log the rate change
		frappe.msgprint(
			f"Interest rate for Loan {self.name} updated from {old_rate}% to {new_rate}%. "
			f"New EMI: ₹{self.emi_amount}"
		)


def process_all_emis():
	"""Scheduled function to process EMIs for all active loan accounts."""
	today_day = getdate(today()).day
	accounts = frappe.get_all(
		"Banking Loan Account",
		filters={
			"account_status": "Active",
			"emi_date": today_day
		}
	)
	for acc in accounts:
		doc = frappe.get_doc("Banking Loan Account", acc.name)
		doc.process_emi()


def post_all_interest():
	"""Scheduled function to post interest for all active loan accounts."""
	accounts = frappe.get_all(
		"Banking Loan Account",
		filters={"account_status": ("in", ["Active", "NPA"])}
	)
	for acc in accounts:
		doc = frappe.get_doc("Banking Loan Account", acc.name)
		doc.post_interest()
