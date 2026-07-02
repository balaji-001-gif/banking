# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, date_diff


class BankingNpaTracker(Document):
	"""Controller for Banking NPA Tracker with auto-classification."""

	def validate(self):
		self.calculate_overdue()
		self.calculate_provision()

	def calculate_overdue(self):
		"""Calculate overdue amount based on loan account EMI."""
		if self.loan_account:
			loan = frappe.get_doc("Banking Loan Account", self.loan_account)
			self.overdue_amount = loan.emi_amount * min(self.days_past_due // 30, 12) if loan.emi_amount else 0

	def calculate_provision(self):
		"""Calculate provisioning as per RBI norms."""
		provision_pcts = {
			"SMA-0": 0,
			"SMA-1": 0.05,
			"SMA-2": 0.10,
			"Sub-standard": 0.15,
			"Doubtful": 0.40,
			"Loss": 1.00
		}
		pct = provision_pcts.get(self.npa_classification, 0)
		self.provision_amount = round(self.overdue_amount * pct, 2)


def auto_classify_npa():
	"""Scheduled function to auto-classify NPA based on DPD.
	
	RBI guidelines:
	- SMA-0: 0-30 DPD
	- SMA-1: 31-60 DPD
	- SMA-2: 61-90 DPD
	- Sub-standard: 91-180 DPD
	- Doubtful: 181-365 DPD (or more)
	- Loss: > 365 DPD or identified as loss
	"""
	trackers = frappe.get_all("Banking NPA Tracker", filters={"loan_account": ("is", "set")})

	for t in trackers:
		tracker = frappe.get_doc("Banking NPA Tracker", t.name)
		loan = frappe.get_doc("Banking Loan Account", tracker.loan_account)

		# Calculate DPD
		if loan.emi_date:
			# Simplified DPD calculation
			last_emi_date = getdate(today()).replace(day=min(loan.emi_date, 28))
			dpd = date_diff(today(), last_emi_date)
			if dpd < 0:
				dpd = 0

			tracker.days_past_due = dpd

			# Classification as per RBI
			if dpd <= 30:
				tracker.npa_classification = "SMA-0"
			elif dpd <= 60:
				tracker.npa_classification = "SMA-1"
			elif dpd <= 90:
				tracker.npa_classification = "SMA-2"
			elif dpd <= 180:
				tracker.npa_classification = "Sub-standard"
			elif dpd <= 365:
				tracker.npa_classification = "Doubtful"
			else:
				tracker.npa_classification = "Loss"

			# Update loan account status
			if dpd > 90:
				loan.db_set("account_status", "NPA")

			tracker.db_set("days_past_due", dpd)
			tracker.db_set("npa_classification", tracker.npa_classification)
			tracker.calculate_overdue()
			tracker.calculate_provision()
			tracker.db_set("overdue_amount", tracker.overdue_amount)
			tracker.db_set("provision_amount", tracker.provision_amount)
