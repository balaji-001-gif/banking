app_name = "bizaxl_banking"
app_title = "Bizaxl Banking"
app_publisher = "Your Organisation"
app_description = "Banking app module with full business logic for ERPNext v15+"
app_email = "you@example.com"
app_license = "MIT"

required_apps = ["frappe", "erpnext"]

# Fixtures -------------------------------------------------------------
fixtures = [
	{"doctype": "Role", "filters": [["role_name", "like", "Banking %"]]}
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
		"bizaxl_banking.banking.doctype.banking_loan_account.banking_loan_account.process_all_emis"
	],
	"monthly_long": [
		"bizaxl_banking.banking.doctype.banking_loan_account.banking_loan_account.post_all_interest"
	]
}
