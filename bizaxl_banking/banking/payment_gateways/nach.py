# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.utils import today, now_datetime
from ..doctype.banking_integration_settings.banking_integration_settings import (
	is_integration_enabled, get_api_key, get_api_secret, get_endpoint_url, get_integration_settings
)

"""
NACH Mandate (NPCI) Integration Module

Handles: NACH mandate registration, modification, cancellation, and auto-debit execution
Requires: NPCI NACH API credentials configured in Banking Integration Settings
"""


def register_mandate(mandate):
	"""Register a NACH mandate with the sponsor bank via NPCI.
	
	Args:
		mandate: Banking NACH Mandate document
		
	Returns:
		dict: Registration result with mandate reference
	"""
	if not is_integration_enabled("nach"):
		return {"status": "disabled", "message": "NACH integration not configured"}

	try:
		endpoint = get_endpoint_url("nach")
		api_key = get_api_key("nach")
		api_secret = get_api_secret("nach")
		settings = get_integration_settings()

		payload = _get_mandate_payload(mandate)

		if api_key and endpoint:
			headers = {
				"Content-Type": "application/json",
				"X-API-Key": api_key,
				"X-API-Secret": api_secret
			}
			response = requests.post(f"{endpoint}/mandates/register", json=payload, headers=headers, timeout=30)
			result = response.json()

			if response.status_code == 200 and result.get("status") == "REGISTERED":
				return {
					"status": "registered",
					"sponsor_ref": result.get("sponsor_reference", ""),
					"mandate_ref": result.get("mandate_reference", ""),
					"registered_at": result.get("registered_at", str(now_datetime()))
				}
			else:
				return {
					"status": "failed",
					"error_message": result.get("message", "NACH registration failed"),
					"mandate_ref": mandate.name
				}
		else:
			# Simulated for development
			return {
				"status": "simulated",
				"sponsor_ref": f"SIMSPON{now_datetime().strftime('%Y%m%d%H%M%S')}",
				"mandate_ref": f"SIMMAN{now_datetime().strftime('%Y%m%d%H%M%S')}",
				"message": "NACH API not configured. Mandate registered locally."
			}

	except Exception as e:
		frappe.log_error(f"NACH registration error: {str(e)}", "NACH Integration")
		return {"status": "error", "error_message": str(e), "mandate_ref": mandate.name}


def _get_mandate_payload(mandate):
	"""Build NACH registration payload from mandate + linked account data."""
	settings = get_integration_settings()
	
	# Resolve customer name and IFSC from linked Banking Account
	customer_name = ""
	ifsc_code = ""
	account_number = mandate.account or ""
	
	if mandate.account:
		try:
			account_doc = frappe.get_cached_doc("Banking Account", mandate.account)
			if account_doc.customer:
				customer_name = frappe.db.get_value("Banking Customer", account_doc.customer, "full_name") or ""
			# Get branch IFSC for the account's home branch
			if account_doc.branch:
				ifsc_code = frappe.db.get_value("Banking Branch", account_doc.branch, "ifsc_code") or ""
		except Exception:
			pass
	
	return {
		"mandate_ref": mandate.name,
		"sponsor_bank_code": settings.get("nach_sponsor_bank") or "",
		"member_id": settings.get("nach_member_id") or "",
		"customer_name": customer_name,
		"account_number": account_number,
		"ifsc_code": ifsc_code,
		"amount": mandate.max_amount or 0,
		"frequency": mandate.frequency if hasattr(mandate, 'frequency') else "Monthly",
		"start_date": str(mandate.start_date) if hasattr(mandate, 'start_date') and mandate.start_date else str(today()),
		"end_date": str(mandate.end_date) if hasattr(mandate, 'end_date') and mandate.end_date else "",
		"debit_type": "001",
		"timestamp": now_datetime().isoformat()
	}


def execute_auto_debit(mandate, amount, narration=""):
	"""Execute auto-debit against a registered NACH mandate.
	
	Args:
		mandate: Banking NACH Mandate document
		amount: Amount to debit
		narration: Optional narration
		
	Returns:
		dict: Debit execution result
	"""
	if not is_integration_enabled("nach"):
		return {"status": "disabled", "message": "NACH auto-debit not configured"}

	try:
		endpoint = get_endpoint_url("nach")
		api_key = get_api_key("nach")

		payload = {
			"mandate_ref": mandate.name,
			"amount_paise": int(amount * 100),
			"narration": narration or "Auto-debit via NACH",
			"transaction_ref": f"NACH-DR-{now_datetime().strftime('%Y%m%d%H%M%S')}",
			"timestamp": now_datetime().isoformat()
		}

		if api_key and endpoint:
			headers = {
				"Content-Type": "application/json",
				"X-API-Key": api_key
			}
			response = requests.post(f"{endpoint}/debit", json=payload, headers=headers, timeout=30)
			result = response.json()

			if response.status_code == 200 and result.get("status") == "DEBITED":
				return {
					"status": "success",
					"utr": result.get("utr", ""),
					"debited_at": result.get("debited_at", str(now_datetime()))
				}
			else:
				return {"status": "failed", "error_message": result.get("message", "Auto-debit failed")}
		else:
			return {"status": "simulated", "utr": f"SIMUTR{now_datetime().strftime('%Y%m%d%H%M%S')}"}

	except Exception as e:
		frappe.log_error(f"NACH auto-debit error: {str(e)}", "NACH Integration")
		return {"status": "error", "error_message": str(e)}


def cancel_mandate(mandate_ref):
	"""Cancel an existing NACH mandate.
	
	Args:
		mandate_ref: Mandate reference number
		
	Returns:
		dict: Cancellation result
	"""
	if not is_integration_enabled("nach"):
		return {"status": "disabled", "message": "NACH integration not configured"}

	try:
		endpoint = get_endpoint_url("nach")

		payload = {"mandate_ref": mandate_ref, "reason": "Customer request"}

		api_key = get_api_key("nach")
		if api_key and endpoint:
			headers = {"X-API-Key": api_key}
			response = requests.post(f"{endpoint}/mandates/cancel", json=payload, headers=headers, timeout=15)
			result = response.json()
			return {"status": "cancelled" if response.status_code == 200 else "failed",
					"message": result.get("message", "")}
		else:
			return {"status": "simulated", "message": "Mandate cancelled locally (API not configured)."}

	except Exception as e:
		frappe.log_error(f"NACH cancellation error: {str(e)}", "NACH Integration")
		return {"status": "error", "error_message": str(e)}
