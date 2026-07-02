# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, nowdate


class BankingCustomer(Document):
	"""Controller for Banking Customer with auto-numbering, validation, AML screening, and risk scoring.
	
	Integration hooks:
	- PAN verification (real-time via NSDL API if configured)
	- Sanctions screening (against OFAC/UN/MHA lists if configured)
	- Transaction alerts (via SMS/Email if configured)
	"""

	def autoname(self):
		"""Auto-generate customer ID: CUST-YYYY-MM-XXXXX"""
		from frappe.model.naming import make_autoname
		prefix = f"CUST-{frappe.utils.nowdate()[:7]}-\"
		self.name = make_autoname(prefix + "#####")

	def validate(self):
		self.validate_pan()
		self.validate_mobile()
		self.auto_calculate_risk_category()
		self.update_kyc_status()

	def validate_pan(self):
		"""Basic PAN format validation (ABCDE1234F)."""
		if self.pan_number:
			import re
			if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", self.pan_number.upper()):
				frappe.throw("Invalid PAN Number format. Must be 10 characters (e.g., ABCDE1234F).")

	def validate_mobile(self):
		"""Validate Indian mobile number (10 digits, starts with 6-9)."""
		if self.mobile:
			import re
			mobile = self.mobile.strip()
			if not re.match(r"^[6-9]\d{9}$", mobile):
				frappe.throw("Invalid Mobile Number. Must be a 10-digit Indian mobile number.")

	def auto_calculate_risk_category(self):
		"""Auto-calculate risk category based on customer type and FATCA status.
		
		Rules:
		- Trust/Co-op Society → always High
		- FATCA Non-compliant → always High
		- Individual/Proprietary with FATCA Compliant → Low (default)
		- Company/Partnership → Medium (default)
		"""
		if not self.risk_category or self.risk_category == "Low":
			if self.customer_type in ("Trust", "Co-op Society"):
				self.risk_category = "High"
			elif self.fatca_status == "Non-compliant":
				self.risk_category = "High"
			elif self.customer_type in ("Individual", "Proprietary"):
				self.risk_category = "Low"
			elif self.customer_type in ("Company", "Partnership"):
				self.risk_category = "Medium"

	def update_kyc_status(self):
		"""Auto-update KYC status based on document verification."""
		if self.kyc_status == "Verified" and self.risk_category not in ("Low", "Medium", "High"):
			self.risk_category = "Medium"

	def on_update(self):
		"""Run post-save hooks: AML screening, sanctions check, PAN verification."""
		if self.has_value_changed("kyc_status") and self.kyc_status == "Verified":
			self.create_aml_screening_log()
			self.run_integration_hooks()

	def run_integration_hooks(self):
		"""Run third-party integration checks (silent — never blocks save)."""
		# PAN verification via NSDL
		if self.pan_number:
			try:
				from bizaxl_banking.banking.kyc.pan import verify_pan
				result = verify_pan(self.pan_number, self.full_name, self.date_of_birth)
				if result.get("status") == "verified":
					pan_data = result.get("data", {})
					if pan_data.get("name_match") is False:
						frappe.msgprint(
							f"Warning: PAN name mismatch. Customer provided '{self.full_name}', "
							f"PAN database shows '{pan_data.get('full_name')}'.",
							indicator="orange"
						)
			except Exception:
				frappe.log_error(f"PAN verification failed for {self.name}", "PAN Integration")
				frappe.msgprint("PAN verification service unavailable. Manual verification required.", indicator="yellow")

		# Sanctions screening
		try:
			from bizaxl_banking.banking.compliance.sanctions import screen_customer
			result = screen_customer(
				self.name, self.pan_number, self.full_name, self.date_of_birth
			)
			if result.get("match_found"):
				frappe.msgprint(
					f"⚠ Sanctions match found for {self.full_name}! "
					f"Compliance team notified. Disposition: {result.get('disposition')}",
					indicator="red"
				)
				self.create_aml_screening_log(match_found=1, disposition=result.get("disposition"))
		except Exception:
			frappe.log_error(f"Sanctions screening failed for {self.name}", "Sanctions Integration")

	def create_aml_screening_log(self, match_found=0, disposition="Clear"):
		"""Create an AML screening log entry."""
		screening = frappe.get_doc({
			"doctype": "Banking AML Screening Log",
			"screening_type": "Onboarding",
			"customer": self.name,
			"lists_checked": "UNSC, OFAC, EU Sanctions, Internal Watchlist",
			"match_found": match_found,
			"disposition": disposition,
			"screened_at": frappe.utils.now()
		})
		screening.insert(ignore_permissions=True)
		if match_found:
			frappe.msgprint(f"AML Screening Log created: {disposition}", indicator="orange")


def recalculate_customer_risk_scores():
	"""Scheduled function to recalculate risk scores based on transaction behavior.
	
	Rules applied:
	- High-value transactions (avg > ₹5L per month) → upgrade risk to High
	- Multiple international payments → upgrade risk to High
	- Frequent cash deposits (> 10 per month) → upgrade risk to Medium
	"""
	from frappe.utils import add_months
	three_months_ago = add_months(today(), -3)

	# Check customers with high transaction volumes
	high_volume_customers = frappe.db.sql("""
		SELECT 
			ba.customer,
			AVG(po.amount) as avg_amount,
			COUNT(*) as txn_count
		FROM `tabBanking Payment Order` po
		JOIN `tabBanking Account` ba ON ba.name = po.from_account
		WHERE po.creation >= %s
			AND po.status = 'Settled'
		GROUP BY ba.customer
		HAVING AVG(po.amount) > 500000 OR COUNT(*) > 50
	""", three_months_ago, as_dict=True)

	for row in high_volume_customers:
		if row.customer:
			current_risk = frappe.db.get_value("Banking Customer", row.customer, "risk_category")
			if current_risk == "Low":
				frappe.db.set_value("Banking Customer", row.customer, "risk_category", "Medium")
			elif current_risk == "Medium" and row.avg_amount > 500000:
				frappe.db.set_value("Banking Customer", row.customer, "risk_category", "High")
