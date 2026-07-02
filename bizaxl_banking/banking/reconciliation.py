# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
import csv
import io
from frappe.utils import today, now_datetime


@frappe.whitelist()
def upload_statement_csv(account, file_url):
	"""Upload and process bank statement CSV file for reconciliation.
	
	Expected CSV columns: txn_date, narration, debit, credit, reference
	
	Returns summary of matched, unmatched, and new entries.
	"""
	file_doc = frappe.get_doc("File", {"file_url": file_url})
	content = file_doc.get_content()
	reader = csv.DictReader(io.StringIO(content))

	matched = 0
	unmatched = 0
	errors = 0

	for row in reader:
		try:
			amount = float(row.get("debit", 0) or 0) or float(row.get("credit", 0) or 0)
			is_debit = float(row.get("debit", 0) or 0) > 0

			# Try to find matching transaction in ledger
			ledger_entries = frappe.get_all(
				"Banking Transaction Ledger",
				filters={
					"account": account,
					"posting_date": row.get("txn_date", today()),
					"debit_amount": float(row.get("debit", 0) or 0) if is_debit else 0,
					"credit_amount": float(row.get("credit", 0) or 0) if not is_debit else 0
				},
				fields=["name", "is_reversed"]
			)

			if ledger_entries:
				matched += 1
			else:
				unmatched += 1

		except Exception as e:
			errors += 1
			frappe.log_error(f"Reconciliation error: {str(e)}", "Bank Statement Reconciliation")

	frappe.msgprint(
		f"Reconciliation complete for account {account}:\n"
		f"✓ {matched} matched\n"
		f"⚠ {unmatched} unmatched (statement entries with no ledger match)\n"
		f"✗ {errors} errors"
	)

	return {
		"account": account,
		"matched": matched,
		"unmatched": unmatched,
		"errors": errors,
		"date": str(today())
	}


def run_daily_reconciliation():
	"""Scheduled daily reconciliation job.
	
	For each active account, check if total settled payments for today
	match the expected balance movement in the ledger.
	Flag accounts with discrepancies.
	"""
	accounts = frappe.get_all("Banking Account", filters={"account_status": "Active"})

	for acc in accounts:
		account_doc = frappe.get_doc("Banking Account", acc.name)

		# Get total payments settled today from this account
		today_payments = frappe.db.sql("""
			SELECT COALESCE(SUM(amount), 0) as total_debited
			FROM `tabBanking Payment Order`
			WHERE from_account = %s
				AND DATE(settled_at) = CURDATE()
				AND status = 'Settled'
		""", acc.name, as_dict=True)[0]

		# Get ledger entries posted today
		today_ledger = frappe.db.sql("""
			SELECT 
				COALESCE(SUM(debit_amount), 0) as total_debit,
				COALESCE(SUM(credit_amount), 0) as total_credit
			FROM `tabBanking Transaction Ledger`
			WHERE account = %s
				AND posting_date = CURDATE()
		""", acc.name, as_dict=True)[0]

		# Calculate expected balance
		expected_balance = account_doc.current_balance - today_payments.total_debited

		# If there's a mismatch, flag it
		actual_balance = account_doc.current_balance
		debit_credit_diff = today_ledger.total_debit - today_ledger.total_credit

		if abs(expected_balance - actual_balance) > 1:  # Allow ₹1 rounding
			frappe.get_doc({
				"doctype": "Banking Fraud Alert",
				"alert_type": "Manual",
				"triggered_on": now_datetime(),
				"account": acc.name,
				"risk_score": 50,
				"auto_hold_applied": 0,
				"status": "Open",
				"description": (
					f"Reconciliation discrepancy for account {acc.name}: "
					f"Expected balance ₹{expected_balance:,.2f}, "
					f"Actual balance ₹{actual_balance:,.2f}. "
					f"Ledger shows net ₹{debit_credit_diff:,.2f} movement today."
				)
			}).insert(ignore_permissions=True)

			frappe.log_error(
				f"Reconciliation mismatch for {acc.name}: "
				f"Expected ₹{expected_balance}, Actual ₹{actual_balance}",
				"Daily Reconciliation"
			)
