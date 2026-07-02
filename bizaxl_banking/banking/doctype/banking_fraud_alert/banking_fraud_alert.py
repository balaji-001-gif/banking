# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, now_datetime, getdate


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
	
	Detection rules:
	1. Velocity Breach — High-value transactions (> ₹10L) or rapid attempts
	2. Unusual Geography — Transaction location differs from branch city
	3. Account Takeover — Multiple failed payment patterns
	4. Positive Pay Mismatch — Checks presented don't match pre-registered details
	"""
	today_str = today()
	from frappe.utils import add_to_date
	one_hour_ago = add_to_date(now_datetime(), hours=-1)

	# ---- 1. VELOCITY BREACH DETECTION ----
	detect_velocity_breach(today_str, one_hour_ago)

	# ---- 2. UNUSUAL GEOGRAPHY DETECTION ----
	detect_unusual_geography(today_str)

	# ---- 3. ACCOUNT TAKEOVER DETECTION ----
	detect_account_takeover(one_hour_ago)

	# ---- 4. POSITIVE PAY MISMATCH DETECTION ----
	detect_positive_pay_mismatch()


def _already_alerted(account, alert_type, since):
	"""Check if an alert of this type already exists for this account."""
	existing = frappe.get_all(
		"Banking Fraud Alert",
		filters={
			"account": account,
			"alert_type": alert_type,
			"creation": (">=", since)
		}
	)
	return len(existing) > 0


def _create_alert(account, alert_type, risk_score, triggered_on=None):
	"""Create a fraud alert."""
	if not triggered_on:
		triggered_on = now_datetime()
	alert = frappe.get_doc({
		"doctype": "Banking Fraud Alert",
		"alert_type": alert_type,
		"triggered_on": triggered_on,
		"account": account,
		"risk_score": risk_score,
		"auto_hold_applied": 0,
		"status": "Open"
	})
	alert.insert(ignore_permissions=True)


# ---- 1. VELOCITY BREACH ----
def detect_velocity_breach(today_str, one_hour_ago):
	"""Detect high-value payments and rapid payment attempts."""
	# High-value payments >= ₹10L
	high_value_payments = frappe.get_all(
		"Banking Payment Order",
		filters={
			"amount": (">=", 1000000),
			"creation": (">=", today_str)
		},
		fields=["name", "from_account", "amount"]
	)
	for payment in high_value_payments:
		if not _already_alerted(payment.from_account, "Velocity Breach", today_str):
			_create_alert(payment.from_account, "Velocity Breach", 65)

	# Rapid payments: >= 5 in 1 hour
	rapid_payments = frappe.db.sql("""
		SELECT from_account, COUNT(*) as cnt
		FROM `tabBanking Payment Order`
		WHERE creation >= %s
		GROUP BY from_account
		HAVING cnt >= 5
	""", one_hour_ago, as_dict=True)

	for row in rapid_payments:
		if not _already_alerted(row.from_account, "Velocity Breach", one_hour_ago):
			_create_alert(row.from_account, "Velocity Breach", 75)


# ---- 2. UNUSUAL GEOGRAPHY ----
def detect_unusual_geography(today_str):
	"""Detect transactions from locations different from the customer's branch city.
	
	Logic: Compare the IFSC code of the receiving bank against the customer's
	branch city. If the receiving bank is in a different city/state than the
	customer's branch, flag as unusual.
	"""
	# Get today's payment orders where the receiving IFSC differs from bank prefix
	# Compare first 4 chars of to_ifsc against first 4 chars of branch's IFSC
	unusual_payments = frappe.db.sql("""
		SELECT 
			po.name,
			po.from_account,
			po.to_ifsc,
			ba.branch as branch_name,
			br.state as branch_state,
			br.branch_name as branch_city
		FROM `tabBanking Payment Order` po
		JOIN `tabBanking Account` ba ON ba.name = po.from_account
		JOIN `tabBanking Branch` br ON br.name = ba.branch
		WHERE po.creation >= %s
			AND po.status IN ('Approved', 'Submitted', 'Settled')
			AND SUBSTRING(po.to_ifsc, 1, 4) != SUBSTRING(br.ifsc_code, 1, 4)
	""", today_str, as_dict=True)

	for payment in unusual_payments:
		if not _already_alerted(payment.from_account, "Unusual Geography", today_str):
			_create_alert(
				payment.from_account,
				"Unusual Geography",
				60,
				now_datetime()
			)
			frappe.db.set_value("Banking Payment Order", payment.name, "status", "Pending Approval")


def detect_account_takeover(one_hour_ago):
	"""Detect potential account takeover based on:
	- Multiple failed/stopped payment orders in short period
	- High number of cancelled payment orders
	"""
	# Failed payment orders in last hour
	failed_payments = frappe.db.sql("""
		SELECT from_account, COUNT(*) as cnt
		FROM `tabBanking Payment Order`
		WHERE creation >= %s
			AND status IN ('Failed', 'Draft')
		GROUP BY from_account
		HAVING cnt >= 3
	""", one_hour_ago, as_dict=True)

	for row in failed_payments:
		if not _already_alerted(row.from_account, "Account Takeover", one_hour_ago):
			_create_alert(row.from_account, "Account Takeover", 70)

	# Cancelled payment orders in last 24 hours
	from frappe.utils import add_to_date
	one_day_ago = add_to_date(now_datetime(), hours=-24)
	cancelled = frappe.db.sql("""
		SELECT from_account, COUNT(*) as cnt
		FROM `tabBanking Payment Order`
		WHERE modified >= %s
			AND docstatus = 2
		GROUP BY from_account
		HAVING cnt >= 3
	""", one_day_ago, as_dict=True)

	for row in cancelled:
		if not _already_alerted(row.from_account, "Account Takeover", one_day_ago):
			_create_alert(row.from_account, "Account Takeover", 65)


# ---- 4. POSITIVE PAY MATCHING ----
def detect_positive_pay_mismatch():
	"""Match incoming cheque payments against Positive Pay records.
	
	When a Payment Order with payment_rail='Cheque' is created, check if
	there's a matching Positive Pay record. If not found or details don't
	match, create a Positive Pay Mismatch alert.
	"""
	# Find cheque-based payment orders that haven't been checked for Positive Pay
	pending_cheques = frappe.get_all(
		"Banking Payment Order",
		filters={
			"payment_rail": "Cheque",
			"status": ("in", ["Draft", "Pending Approval"]),
			"docstatus": 0
		},
		fields=["name", "from_account", "amount", "to_account_no", "narration"]
	)

	for cheque in pending_cheques:
		# Try to find a matching Positive Pay record
		matching_records = frappe.get_all(
			"Banking Positive Pay Record",
			filters={
				"account": cheque.from_account,
				"cheque_number": cheque.to_account_no,
				"status": "Pending"
			},
			fields=["name", "amount", "payee_name"]
		)

		if not matching_records:
			# No Positive Pay record found — this is a mismatch
			if not _already_alerted(cheque.from_account, "Positive Pay Mismatch", today()):
				_create_alert(cheque.from_account, "Positive Pay Mismatch", 85)
				frappe.db.set_value("Banking Payment Order", cheque.name, "status", "Failed")
		else:
			# Record found — check amount match
			for record in matching_records:
				if abs(record.amount - cheque.amount) > 0.01:
					# Amount mismatch
					if not _already_alerted(cheque.from_account, "Positive Pay Mismatch", today()):
						_create_alert(cheque.from_account, "Positive Pay Mismatch", 80)
					frappe.db.set_value("Banking Positive Pay Record", record.name, "status", "Mismatch")
				else:
					# Match successful
					frappe.db.set_value("Banking Positive Pay Record", record.name, {
						"status": "Matched",
						"matched_on": now_datetime()
					})
