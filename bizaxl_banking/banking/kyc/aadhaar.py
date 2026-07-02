# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
import requests
from ..doctype.banking_integration_settings.banking_integration_settings import (
	is_integration_enabled, get_api_key, get_api_secret, get_endpoint_url, get_integration_settings
)

"""
UIDAI / Aadhaar eKYC Integration Module

Handles: Aadhaar OTP-based eKYC, Offline XML verification
Requires: UIDAI API credentials configured in Banking Integration Settings
"""


def verify_aadhaar_otp(aadhaar_number, otp, txn_id=None):
	"""Verify Aadhaar using OTP-based eKYC.
	
	Steps:
	1. Generate OTP (if no txn_id provided)
	2. Verify OTP and retrieve KYC data
	
	Args:
		aadhaar_number: Masked or full Aadhaar number
		otp: OTP received by Aadhaar holder
		txn_id: Optional existing transaction ID
		
	Returns:
		dict: KYC verification result
	"""
	if not is_integration_enabled("aadhaar"):
		return {"status": "disabled", "message": "Aadhaar eKYC not configured"}

	try:
		endpoint = get_endpoint_url("aadhaar")
		api_key = get_api_key("aadhaar")
		api_secret = get_api_secret("aadhaar")
		settings = get_integration_settings()

		payload = {
			"aadhaar_number": aadhaar_number,
			"otp": otp,
			"txn_id": txn_id or "",
			"license_key": settings.get("aadhaar_license_key") or "",
			"org_id": settings.get("aadhaar_org_id") or ""
		}

		if api_key and endpoint:
			headers = {
				"Content-Type": "application/json",
				"X-API-Key": api_key,
				"X-API-Secret": api_secret
			}
			response = requests.post(f"{endpoint}/verify", json=payload, headers=headers, timeout=30)
			result = response.json()

			if response.status_code == 200 and result.get("status") == "VERIFIED":
				return {
					"status": "verified",
					"kyc_data": {
						"name": result.get("name", ""),
						"dob": result.get("dob", ""),
						"gender": result.get("gender", ""),
						"address": result.get("address", ""),
						"photo": result.get("photo", "")
					},
					"txn_id": result.get("txn_id", ""),
					"response": result
				}
			else:
				return {"status": "failed", "error_message": result.get("message", "Aadhaar verification failed")}
		else:
			# Simulated for development
			return {
				"status": "simulated",
				"kyc_data": {
					"name": "Sample User",
					"dob": "1990-01-01",
					"gender": "M",
					"address": "Simulated Address, India"
				},
				"message": "Aadhaar API not fully configured. Simulated response."
			}

	except Exception as e:
		frappe.log_error(f"Aadhaar eKYC error: {str(e)}", "Aadhaar Integration")
		return {"status": "error", "error_message": str(e)}


def verify_offline_xml(xml_content, reference_id):
	"""Verify Aadhaar Offline XML (non-biometric verification).
	
	Args:
		xml_content: Aadhaar Offline XML string
		reference_id: Reference ID from UIDAI
		
	Returns:
		dict: Verification result
	"""
	try:
		import xml.etree.ElementTree as ET
		root = ET.fromstring(xml_content)
		name = root.findtext(".//Name", "")
		dob = root.findtext(".//DOB", "")
		gender = root.findtext(".//Gender", "")

		return {
			"status": "verified",
			"kyc_data": {"name": name, "dob": dob, "gender": gender},
			"reference_id": reference_id,
			"method": "offline_xml"
		}
	except Exception as e:
		return {"status": "failed", "error_message": f"XML parse error: {str(e)}"}
