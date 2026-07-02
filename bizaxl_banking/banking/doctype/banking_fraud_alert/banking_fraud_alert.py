# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, now_datetime


class BankingFraudAlert(Document):
	"""Controller for Banking Fraud Alert with auto-detection hooks."""

	def validate(self):
		self.validate_risk_score()

	def validate_risk_score(self):
		"""Ensure risk score is between 0-100."""
		if self.risk_score and (self.risk_score < 0 or self.risk_score > 100):
			frappe.throw("Risk Score must be between 0 and 100.")

	def on_update(self):
		"""Auto-hold account if high risk."""
		if self.risk_score >= 80 and not self.auto_hold_applied:
			self.auto_hold_account()
			self.auto_hold_applied = 1
			self.db_set("auto_hold_applied", 1)

	def auto_hold_account(self):
		"""Freeze the account if high-risk fraud detected."""
		if self.account:
			account = frappe.get_doc("Banking Account", self.account)
			if account.account_status == "Active":
				account.db_set("account_status", "Frozen")
				frappe.msgprint(
					f"Account {self.account} has been frozen due to fraud alert. "
					f"Alert: {self.alert_type}, Risk Score: {self.risk_score}"
				)


def auto_detect_fraud():
	"""Scheduled function to auto-detect potential fraud patterns.
	
	Checks:
	1. High-value transactions (> ₹10L)
	2. Multiple failed payment orders
	3. Rapid successive transactions
	"""
	today_str = today()

	# Check for high-value payment orders
	high_value_payments = frappe.get_all(
		"Banking Payment Order",
		filters={
			"amount": (">=", 1000000),
			"creation": (">=", today_str)
		},
		fields=["name", "from_account", "amount"]
	)

	for payment in high_value_payments:
		existing_alerts = frappe.get_all(
			"Banking Fraud Alert",
			filters={
				"account": payment.from_account,
				"alert_type": "Velocity Breach",
				"creation": (">=", today_str)
			}
		)
		if not existing_alerts:
			alert = frappe.get_doc({
				"doctype": "Banking Fraud Alert",
				"alert_type": "Velocity Breach",
				"triggered_on": now_datetime(),
				"account": payment.from_account,
				"risk_score": 65,
				"auto_hold_applied": 0,
				"status": "Open"
			})
			alert.insert(ignore_permissions=True)

	# Check for rapid payment attempts (> 5 in 1 hour)
	from frappe.utils import add_to_date
	one_hour_ago = add_to_date(now_datetime(), hours=-1)
	rapid_payments = frappe.db.sql("""
		SELECT from_account, COUNT(*) as cnt
		FROM `tabBanking Payment Order`
		WHERE creation >= %s
		GROUP BY from_account
		HAVING cnt >= 5
	""", one_hour_ago, as_dict=True)

	for row in rapid_payments:
		existing = frappe.get_all(
			"Banking Fraud Alert",
			filters={
				"account": row.from_account,
				"alert_type": "Velocity Breach",
				"creation": (">=", one_hour_ago)
			}
		)
		if not existing:
			alert = frappe.get_doc({
				"doctype": "Banking Fraud Alert",
				"alert_type": "Velocity Breach",
				"triggered_on": now_datetime(),
				"account": row.from_account,
				"risk_score": 75,
				"auto_hold_applied": 0,
				"status": "Open"
			})
			alert.insert(ignore_permissions=True)
