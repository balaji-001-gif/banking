# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
import requests
from ..doctype.banking_integration_settings.banking_integration_settings import (
	is_integration_enabled, get_api_key, get_api_secret, get_endpoint_url, get_integration_settings
)

"""
NSDL / PAN Verification Integration Module

Handles: Real-time PAN validation, name match, and income-tax linkage
Requires: NSDL PAN API credentials configured in Banking Integration Settings
"""


def verify_pan(pan_number, full_name=None, date_of_birth=None):
	"""Verify PAN card details in real-time.
	
	Args:
		pan_number: 10-character PAN (ABCDE1234F)
		full_name: Optional name to match against PAN database
		date_of_birth: Optional DOB to match against PAN database
		
	Returns:
		dict: Verification result with PAN owner details
	"""
	if not is_integration_enabled("pan"):
		return {"status": "disabled", "message": "PAN verification not configured"}

	try:
		endpoint = get_endpoint_url("pan")
		api_key = get_api_key("pan")
		api_secret = get_api_secret("pan")
		settings = get_integration_settings()

		payload = {
			"pan": pan_number.upper(),
			"merchant_code": settings.get("pan_merchant_code") or ""
		}

		if api_key and endpoint:
			headers = {
				"Content-Type": "application/json",
				"X-API-Key": api_key,
				"X-API-Secret": api_secret
			}
			response = requests.post(f"{endpoint}/verify", json=payload, headers=headers, timeout=15)
			result = response.json()

			if response.status_code == 200 and result.get("is_valid"):
				pan_data = {
					"pan": result.get("pan", pan_number.upper()),
					"full_name": result.get("name", ""),
					"date_of_birth": result.get("dob", ""),
					"pan_status": result.get("status", ""),
					"is_valid": True
				}

				# Name match validation
				if full_name and pan_data["full_name"]:
					name_match = full_name.upper().strip() == pan_data["full_name"].upper().strip()
					pan_data["name_match"] = name_match

				# DOB match validation
				if date_of_birth and pan_data["date_of_birth"]:
					pan_data["dob_match"] = str(date_of_birth) == str(pan_data["date_of_birth"])

				return {"status": "verified", "data": pan_data}
			else:
				return {
					"status": "failed",
					"error_message": result.get("message", "PAN verification failed"),
					"data": {"pan": pan_number.upper(), "is_valid": False}
				}
		else:
			# Simulated for development
			return {
				"status": "simulated",
				"data": {
					"pan": pan_number.upper(),
					"full_name": full_name or "SIMULATED NAME",
					"date_of_birth": str(date_of_birth) if date_of_birth else "1990-01-01",
					"is_valid": True,
					"name_match": True,
					"dob_match": True
				},
				"message": "PAN API not fully configured. Simulated response."
			}

	except Exception as e:
		frappe.log_error(f"PAN verification error: {str(e)}", "PAN Integration")
		return {"status": "error", "error_message": str(e)}
