# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class BankingInterestRateSchedule(Document):
	"""Controller for Banking Interest Rate Schedule with slab-based rate computation."""
	
	def validate(self):
		self.validate_amounts()

	def validate_amounts(self):
		"""Ensure minimum amount is less than maximum amount."""
		if self.min_amount and self.max_amount and self.min_amount >= self.max_amount:
			frappe.throw("Minimum Amount must be less than Maximum Amount.")

	@frappe.whitelist()
	def get_applicable_rate(self, amount, tenure_days=None):
		"""Get applicable interest rate for a given amount and tenure."""
		rates = frappe.get_all(
			"Banking Interest Rate Schedule",
			filters={
				"product_type": self.product_type,
				"min_amount": ("<=", amount),
				"max_amount": (">=", amount),
				"is_active": 1
			},
			fields=["interest_rate", "min_tenure_days", "max_tenure_days"],
			order_by="interest_rate desc"
		)
		for rate in rates:
			if tenure_days:
				if rate.min_tenure_days and rate.max_tenure_days:
					if rate.min_tenure_days <= tenure_days <= rate.max_tenure_days:
						return rate.interest_rate
				elif rate.min_tenure_days and tenure_days >= rate.min_tenure_days:
					return rate.interest_rate
				elif rate.max_tenure_days and tenure_days <= rate.max_tenure_days:
					return rate.interest_rate
			else:
				return rate.interest_rate
		return None

	@frappe.whitelist()
	def calculate_interest(self, principal, tenure_days):
		"""Calculate interest amount for given principal and tenure."""
		rate = self.get_applicable_rate(principal, tenure_days)
		if rate:
			return round(principal * rate / 100 * tenure_days / 365, 2)
		return 0
