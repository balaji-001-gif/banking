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
	{"doctype": "Banking Deposit Product", "filters": [["product_name", "like", "%"]]},
	{"doctype": "Banking Interest Rate Schedule", "filters": [["product_type", "like", "%"]]},
	{"doctype": "Banking State", "filters": [["state_name", "like", "%"]]},
	{"doctype": "Banking Integration Settings"},
	{"doctype": "Notification", "filters": [["module", "=", "Banking"]]},
	{"doctype": "Banking Configuration"},
	{"doctype": "Banking Branch", "filters": [["branch_code", "like", "%"]]},
	{"doctype": "Banking Service Charge Rule", "filters": [["charge_type", "like", "%"]]},
	{"doctype": "Banking Customer", "filters": [["full_name", "like", "%"]]},
	{"doctype": "Banking Customer Lead", "filters": [["full_name", "like", "%"]]},
	{"doctype": "Banking KYC Document", "filters": [["document_type", "like", "%"]]},
	{"doctype": "Banking Account", "filters": [["account_number", "like", "%"]]},
	{"doctype": "Banking Account Entitlement", "filters": [["access_level", "like", "%"]]},
	{"doctype": "Banking Standing Instruction", "filters": [["instruction_type", "like", "%"]]},
	{"doctype": "Banking NACH Mandate", "filters": [["mandate_ref", "like", "%"]]},
	{"doctype": "Banking Payment Order", "filters": [["payment_ref", "like", "%"]]},
	{"doctype": "Banking Transaction Ledger", "filters": [["source_docname", "like", "%"]]},
	{"doctype": "Banking Loan Application", "filters": [["loan_product", "like", "%"]]},
	{"doctype": "Banking Loan Account", "filters": [["loan_account_no", "like", "%"]]},
	{"doctype": "Banking Collateral", "filters": [["collateral_type", "like", "%"]]},
	{"doctype": "Banking Fraud Alert", "filters": [["alert_type", "like", "%"]]},
	{"doctype": "Banking Dispute Case", "filters": [["dispute_type", "like", "%"]]},
	{"doctype": "Banking AML Screening Log", "filters": [["screening_type", "like", "%"]]},
	{"doctype": "Banking NPA Tracker", "filters": [["npa_classification", "like", "%"]]},
	{"doctype": "Banking Positive Pay Record", "filters": [["cheque_number", "like", "%"]]},
	{"doctype": "Banking Regulatory Report", "filters": [["report_type", "like", "%"]]},
	{"doctype": "Banking Bulk Payment", "filters": [["batch_reference", "like", "%"]]}
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
