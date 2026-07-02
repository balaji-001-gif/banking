# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

app_name = "bizaxl_banking"
app_title = "Bizaxl Banking"
app_publisher = "Your Organisation"
app_description = "Banking app module with full business logic for ERPNext v15+"
app_email = "you@example.com"
app_license = "MIT"

required_apps = ["frappe", "erpnext"]

# Fixtures -------------------------------------------------------------
fixtures = [
	{"doctype": "Role", "filters": [["role_name", "like", "Banking %"]]},
	{"doctype": "Banking Interest Rate Schedule", "filters": [["product_type", "like", "%"]]}
]

# Scheduled Tasks ------------------------------------------------------
# Note: Document event hooks (validate, on_submit, on_cancel, on_update)
# are handled directly by class methods in each Document subclass.
# Frappe calls them automatically — no doc_events entries needed.

scheduler_events = {
	"daily_long": [
		"bizaxl_banking.banking.doctype.banking_npa_tracker.banking_npa_tracker.auto_classify_npa",
		"bizaxl_banking.banking.doctype.banking_standing_instruction.banking_standing_instruction.process_due_instructions",
		"bizaxl_banking.banking.doctype.banking_fraud_alert.banking_fraud_alert.auto_detect_fraud",
		"bizaxl_banking.banking.doctype.banking_loan_account.banking_loan_account.process_all_emis",
		"bizaxl_banking.banking.doctype.banking_dispute_case.banking_dispute_case.auto_escalate_overdue_disputes",
		"bizaxl_banking.banking.doctype.banking_kyc_document.banking_kyc_document.check_kyc_reverification_due",
		"bizaxl_banking.banking.doctype.banking_account.banking_account.auto_classify_dormant_accounts",
		"bizaxl_banking.banking.doctype.banking_customer.banking_customer.recalculate_customer_risk_scores",
		"bizaxl_banking.banking.doctype.banking_bulk_payment.banking_bulk_payment.process_pending_bulk_payments",
		"bizaxl_banking.banking.reconciliation.run_daily_reconciliation"
	],
	"monthly_long": [
		"bizaxl_banking.banking.doctype.banking_loan_account.banking_loan_account.post_all_interest"
	],
	"weekly_long": [
		"bizaxl_banking.banking.doctype.banking_regulatory_report.banking_regulatory_report.generate_scheduled_reports"
	]
}
