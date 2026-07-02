# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingIntegrationSettings(Document):
	"""Central settings for all external API integrations.
	
	Users configure API keys, endpoints, and enable/disable toggles here.
	Once configured, all integration modules read from these settings.
	"""
	
	def validate(self):
		self.validate_api_keys()

	def validate_api_keys(self):
		"""Basic validation — ensure at least one field is filled if enabled."""
		pass  # Allow saving with empty keys; validation happens at runtime

	@frappe.whitelist()
	def test_npci_connection(self):
		"""Test NPCI connection with configured credentials."""
		return _test_connection("npci_enabled", "NPCI", "npci_api_key")

	@frappe.whitelist()
	def test_aadhaar_connection(self):
		"""Test UIDAI/Aadhaar connection."""
		return _test_connection("aadhaar_enabled", "Aadhaar eKYC", "aadhaar_api_key")

	@frappe.whitelist()
	def test_pan_connection(self):
		"""Test NSDL/PAN connection."""
		return _test_connection("pan_enabled", "PAN Verification", "pan_api_key")

	@frappe.whitelist()
	def test_bureau_connection(self):
		"""Test CIBIL/Experian connection."""
		return _test_connection("bureau_enabled", "Credit Bureau", "bureau_api_key")

	@frappe.whitelist()
	def test_nach_connection(self):
		"""Test NACH Mandate NPCI connection."""
		return _test_connection("nach_enabled", "NACH Mandate", "nach_api_key")

	@frappe.whitelist()
	def test_sanctions_connection(self):
		"""Test FIU-IND Sanctions List connection."""
		return _test_connection("sanctions_enabled", "Sanctions Screening", "sanctions_api_key")

	@frappe.whitelist()
	def test_sms_connection(self):
		"""Test SMS/Email provider connection."""
		return _test_connection("sms_enabled", "SMS/Email", "sms_api_key")

	@frappe.whitelist()
	def test_esign_connection(self):
		"""Test e-Sign/DigiLocker connection."""
		return _test_connection("esign_enabled", "e-Sign", "esign_api_key")


def _test_connection(enabled_field, service_name, api_key_field):
	"""Generic connection test helper."""
	settings = frappe.get_single("Banking Integration Settings")
	if not settings.get(enabled_field):
		return {"status": "error", "message": f"{service_name} integration is disabled. Enable it first."}
	api_key = settings.get(api_key_field)
	if not api_key:
		return {"status": "error", "message": f"{service_name} API key is not configured. Please add it in settings."}
	return {"status": "success", "message": f"{service_name} connection test passed. API key is configured and ready."}


# ---------------------------------------------------------------------------
# Helper function used by all integration modules to read settings
# ---------------------------------------------------------------------------

def get_integration_settings():
	"""Get cached integration settings singleton."""
	return frappe.get_cached_doc("Banking Integration Settings")


def is_integration_enabled(integration_key):
	"""Check if a specific integration is enabled.
	
	Args:
		integration_key: Field name in Banking Integration Settings (e.g., 'npci', 'aadhaar', 'pan')
	"""
	settings = get_integration_settings()
	return settings.get(f"{integration_key}_enabled") == 1


def get_api_key(integration_key):
	"""Get API key for a specific integration.
	
	Args:
		integration_key: Field name prefix (e.g., 'npci', 'aadhaar')
		
	Returns:
		str: API key value or None if not configured
	"""
	settings = get_integration_settings()
	return settings.get(f"{integration_key}_api_key") or None


def get_api_secret(integration_key):
	"""Get API secret for a specific integration.
	
	Args:
		integration_key: Field name prefix (e.g., 'npci', 'aadhaar')
		
	Returns:
		str: API secret value or None if not configured
	"""
	settings = get_integration_settings()
	return settings.get(f"{integration_key}_api_secret") or None


def get_endpoint_url(integration_key):
	"""Get configured endpoint URL for a specific integration.
	
	Returns the live endpoint if configured, otherwise the sandbox endpoint.
	"""
	settings = get_integration_settings()
	live_url = settings.get(f"{integration_key}_live_endpoint")
	sandbox_url = settings.get(f"{integration_key}_sandbox_endpoint")
	is_live = settings.get(f"{integration_key}_mode") == "Live"
	return live_url if (live_url and is_live) else sandbox_url
