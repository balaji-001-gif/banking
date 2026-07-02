# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, add_days, today


class BankingKycDocument(Document):
	"""Controller for Banking KYC Document with expiry tracking and re-verification."""

	def validate(self):
		self.validate_expiry()
		self.auto_update_customer_status()

	def validate_expiry(self):
		"""Warn if document is expired or expiring soon.
		Auto-trigger Re-KYC on customer if document is expired.
		"""
		if self.expiry_date:
			days_until_expiry = date_diff(getdate(self.expiry_date), getdate())
			if days_until_expiry < 0:
				frappe.msgprint(
					f"Warning: Document {self.document_type} (No. {self.document_number}) has expired. "
					f"Customer KYC status will be set to Re-KYC Due."
				)
				# Auto-update customer status to Re-KYC Due
				if self.customer:
					frappe.db.set_value("Banking Customer", self.customer, "kyc_status", "Re-KYC Due")
			elif days_until_expiry <= 30:
				frappe.msgprint(
					f"Warning: Document {self.document_type} (No. {self.document_number}) "
					f"is expiring in {days_until_expiry} days."
				)

	def auto_update_customer_status(self):
		"""Auto-update customer KYC status on document verification."""
		if self.verification_status == "Verified" and self.customer:
			customer = frappe.get_doc("Banking Customer", self.customer)
			if customer.kyc_status in ("Pending", "Re-KYC Due"):
				customer.db_set("kyc_status", "Verified")


def check_kyc_reverification_due():
	"""Scheduled function to check for expired KYC documents and flag customers.
	
	If any KYC document has expired, the customer's KYC status is set to Re-KYC Due.
	If all KYC documents have been expired for 90+ days, the account should be frozen.
	"""
	expired_docs = frappe.get_all(
		"Banking KYC Document",
		filters={
			"expiry_date": ("<", today()),
			"verification_status": "Verified"
		},
		fields=["customer", "name", "expiry_date"]
	)

	processed_customers = set()
	for doc in expired_docs:
		if doc.customer and doc.customer not in processed_customers:
			processed_customers.add(doc.customer)
			frappe.db.set_value("Banking Customer", doc.customer, "kyc_status", "Re-KYC Due")

			# Check if all docs expired for 90+ days → freeze account
			days_expired = date_diff(getdate(), getdate(doc.expiry_date))
			if days_expired >= 90:
				accounts = frappe.get_all("Banking Account", filters={"customer": doc.customer})
				for acc in accounts:
					if frappe.db.get_value("Banking Account", acc.name, "account_status") == "Active":
						frappe.db.set_value("Banking Account", acc.name, "account_status", "Frozen")
						frappe.msgprint(
							f"Account {acc.name} frozen due to KYC documents expired for 90+ days."
						)
