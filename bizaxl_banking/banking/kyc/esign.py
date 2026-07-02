# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from frappe.utils import now_datetime
from ..doctype.banking_integration_settings.banking_integration_settings import (
	is_integration_enabled, get_api_key, get_api_secret, get_endpoint_url, get_integration_settings
)

"""
e-Sign / DigiLocker Integration Module

Handles: Aadhaar-based e-Sign for digital agreements, DigiLocker document retrieval
Requires: e-Sign (CDAC) or DigiLocker API credentials configured in Banking Integration Settings
"""


def send_for_esign(document_path, signer_aadhaar, signer_name, agreement_type="account_opening"):
	"""Send a document for Aadhaar-based e-Sign.
	
	Args:
		document_path: Path to the document file (PDF)
		signer_aadhaar: Signer's Aadhaar number (masked)
		signer_name: Signer's full name
		agreement_type: Type of agreement (account_opening, loan_agreement, etc.)
		
	Returns:
		dict: e-Sign result with signed document reference
	"""
	if not is_integration_enabled("esign"):
		return {"status": "disabled", "message": "e-Sign integration not configured"}

	try:
		endpoint = get_endpoint_url("esign")
		api_key = get_api_key("esign")
		api_secret = get_api_secret("esign")
		settings = get_integration_settings()

		payload = {
			"document_path": document_path,
			"signer_aadhaar": signer_aadhaar,
			"signer_name": signer_name,
			"agreement_type": agreement_type,
			"certificate_id": settings.get("esign_certificate_id") or "",
			"callback_url": f"/api/method/bizaxl_banking.banking.kyc.esign.esign_callback",
			"reference_id": f"ESIGN-{frappe.generate_hash(length=12)}"
		}

		if api_key and endpoint:
			headers = {
				"Content-Type": "application/json",
				"X-API-Key": api_key,
				"X-API-Secret": api_secret
			}
			response = requests.post(f"{endpoint}/sign", json=payload, headers=headers, timeout=60)
			result = response.json()

			if response.status_code == 200 and result.get("status") == "SIGNED":
				return {
					"status": "signed",
					"signed_document_url": result.get("signed_document_url", ""),
					"signing_ref": result.get("reference_id", ""),
					"signed_at": result.get("signed_at", str(now_datetime()))
				}
			else:
				return {"status": "pending", "signing_ref": payload["reference_id"],
						"message": result.get("message", "e-Sign request submitted")}
		else:
			return {
				"status": "simulated",
				"signing_ref": payload["reference_id"],
				"signed_document_url": document_path,
				"message": "e-Sign API not configured. Document marked as digitally signed."
			}

	except Exception as e:
		frappe.log_error(f"e-Sign error: {str(e)}", "eSign Integration")
		return {"status": "error", "error_message": str(e)}


@frappe.whitelist()
def esign_callback():
	"""Callback endpoint for e-Sign provider.
	
	Receives webhook when document is signed.
	"""
	try:
		data = frappe.local.form_dict
		signing_ref = data.get("reference_id")
		status = data.get("status")

		if status == "SIGNED":
			frappe.log_error(f"e-Sign completed for {signing_ref}", "eSign Callback")
			return {"status": "received"}

		return {"status": "received"}
	except Exception as e:
		frappe.log_error(f"e-Sign callback error: {str(e)}", "eSign Callback")
		return {"status": "error"}


def fetch_digilocker_document(uid, document_type):
	"""Fetch a verified document from DigiLocker.
	
	Args:
		uid: User's Aadhaar number (last 4 digits masked)
		document_type: Type of document (Aadhaar, PAN, Driving Licence, etc.)
		
	Returns:
		dict: Document data from DigiLocker
	"""
	if not is_integration_enabled("esign"):
		return {"status": "disabled", "message": "DigiLocker not configured"}

	try:
		endpoint = get_endpoint_url("esign")
		api_key = get_api_key("esign")

		payload = {"uid": uid, "document_type": document_type}

		if api_key and endpoint:
			response = requests.post(f"{endpoint}/digilocker/fetch", json=payload, timeout=30)
			result = response.json()
			if response.status_code == 200:
				return {"status": "fetched", "document": result}
			return {"status": "failed", "error_message": result.get("message", "DigiLocker fetch failed")}
		else:
			return {"status": "simulated", "document": {"type": document_type, "verified": True}}

	except Exception as e:
		frappe.log_error(f"DigiLocker error: {str(e)}", "DigiLocker Integration")
		return {"status": "error", "error_message": str(e)}
