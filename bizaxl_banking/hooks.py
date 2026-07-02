app_name = "bizaxl_banking"
app_title = "Bizaxl Banking"
app_publisher = "Your Organisation"
app_description = "Banking app module scaffold (schema-level) generated from spec, for ERPNext v15+"
app_email = "you@example.com"
app_license = "MIT"

# This app assumes it is installed alongside ERPNext (uses core Currency,
# Bank, and User doctypes as Link targets). If you don't have ERPNext
# installed, remove/replace those Link options in the DocType JSONs.
required_apps = ["frappe", "erpnext"]

# Fixtures -------------------------------------------------------------
# Exports the custom Roles created for this module on `bench export-fixtures`
fixtures = [
	{"doctype": "Role", "filters": [["role_name", "like", "Banking %"]]}
]
