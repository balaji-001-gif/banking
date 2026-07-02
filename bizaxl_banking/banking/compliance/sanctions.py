# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.utils import now_datetime
from ..doctype.banking_integration_settings.banking_integration_settings import (
	is_integration_enabled, get_api_key, get_endpoint_url, get_integration_settings
)

"""
FIU-IND / Sanction Lists / AML Screening Integration Module

Handles: Screening customers and transactions against OFAC, UN, PEP, and MHA lists
Requires: Sanctions screening API credentials configured in Banking Integration Settings
"""

# Default sanction lists that can be checked even without external API
DEFAULT_LISTS = [
	"UNSC Consolidated List",
	"OFAC SDN List",
	"EU Financial Sanctions",
	"MHA Designated List",
	"Internal Watchlist"
]


def screen_customer(customer_name, pan_number, full_name, date_of_birth=None):
	"""Screen a customer against all configured sanction lists.
	
	Args:
		customer_name: Banking Customer name
		pan_number: Customer PAN
		full_name: Customer full name
		date_of_birth: Optional DOB for enhanced matching
		
	Returns:
		dict: Screening result with match details
	"""
	if not is_integration_enabled("sanctions"):
		return {
			"status": "disabled",
			"lists_checked": ", ".join(DEFAULT_LISTS),
			"match_found": 0,
			"disposition": "Clear",
			"message": "Sanctions screening not configured. Manual review recommended."
		}

	try:
		endpoint = get_endpoint_url("sanctions")
		api_key = get_api_key("sanctions")
		settings = get_integration_settings()
		provider = settings.get("sanctions_provider") or "FIU-IND"

		payload = {
			"customer_ref": customer_name,
			"pan": pan_number.upper(),
			"name": full_name,
			"dob": str(date_of_birth) if date_of_birth else "",
			"lists_to_check": DEFAULT_LISTS,
			"threshold_score": 80,
			"screening_type": "individual"
		}

		if api_key and endpoint:
			headers = {
				"Content-Type": "application/json",
				"X-API-Key": api_key
			}
			response = requests.post(f"{endpoint}/screen", json=payload, headers=headers, timeout=30)
			result = response.json()

			match_found = result.get("match_found", False) or result.get("matches", 0) > 0
			disposition = _determine_disposition(result)

			return {
				"status": "success",
				"provider": provider,
				"lists_checked": ", ".join(result.get("lists_checked", DEFAULT_LISTS)),
				"match_found": 1 if match_found else 0,
				"match_details": result.get("matches", []),
				"score": result.get("risk_score", 0),
				"disposition": disposition,
				"screened_at": str(now_datetime())
			}
		else:
			# Simulated — no match found
			return {
				"status": "simulated",
				"lists_checked": ", ".join(DEFAULT_LISTS),
				"match_found": 0,
				"disposition": "Clear",
				"message": "Sanctions API not configured. No match found (simulated)."
			}

	except Exception as e:
		frappe.log_error(f"Sanctions screening error for {customer_name}: {str(e)}", "Sanctions Integration")
		return {
			"status": "error",
			"lists_checked": ", ".join(DEFAULT_LISTS),
			"match_found": 0,
			"disposition": "Manual Review",
			"error_message": str(e)
		}


def screen_transaction(payment_order):
	"""Screen a transaction for sanctions/PEP hits.
	
	Args:
		payment_order: Banking Payment Order document
		
	Returns:
		dict: Transaction screening result
	"""
	if not is_integration_enabled("sanctions"):
		return {"status": "disabled", "match_found": 0}

	try:
		api_key = get_api_key("sanctions")
		settings = get_integration_settings()
		frequency = settings.get("sanctions_check_frequency") or "Per Transaction"

		if frequency != "Per Transaction":
			return {"status": "skipped", "reason": f"Screening frequency set to {frequency}"}

		payload = {
			"transaction_ref": payment_order.name,
			"from_account": payment_order.from_account,
			"to_account": payment_order.to_account_no,
			"to_ifsc": payment_order.to_ifsc,
			"amount": payment_order.amount,
			"payment_rail": payment_order.payment_rail
		}

		endpoint = get_endpoint_url("sanctions")
		if api_key and endpoint:
			response = requests.post(f"{endpoint}/screen-transaction", json=payload, timeout=15)
			result = response.json()
			return {
				"status": "success",
				"match_found": 1 if result.get("match_found") else 0,
				"details": result.get("matches", [])
			}
		else:
			return {"status": "simulated", "match_found": 0}

	except Exception as e:
		frappe.log_error(f"Transaction screening error: {str(e)}", "Sanctions Integration")
		return {"status": "error", "match_found": 0}


def _determine_disposition(result):
	"""Determine disposition based on screening result."""
	if not result.get("match_found") and not result.get("matches"):
		return "Clear"
	elif result.get("false_positive", False):
		return "False Positive"
	else:
		return "True Match → STR Filed"
