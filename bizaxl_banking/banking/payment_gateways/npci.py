# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
import json
import requests
from frappe.utils import now_datetime
from ..doctype.banking_integration_settings.banking_integration_settings import (
	get_integration_settings, is_integration_enabled, get_api_key, get_api_secret, get_endpoint_url
)

"""
NPCI / UPI Rails Integration Module

Handles: UPI, IMPS, NEFT, RTGS payment execution
Requires: NPCI API credentials configured in Banking Integration Settings
"""


def execute_payment(payment_order):
	"""Execute a payment order through NPCI.
	
	Supports rails: UPI, IMPS, NEFT, RTGS
	
	Args:
		payment_order: Banking Payment Order document (submitted/updated)
		
	Returns:
		dict: {
			"status": "success" | "failed" | "disabled",
			"utr_number": str (if success),
			"settled_at": str (if success),
			"error_message": str (if failed)
		}
	"""
	if not is_integration_enabled("npci"):
		return {
			"status": "disabled",
			"message": "NPCI integration not configured. Payment recorded locally."
		}

	try:
		api_key = get_api_key("npci")
		api_secret = get_api_secret("npci")
		endpoint = get_endpoint_url("npci")
		settings = get_integration_settings()

		payload = {
			"merchant_code": settings.get("npci_merchant_code") or "",
			"terminal_id": settings.get("npci_terminal_id") or "",
			"transaction_ref": payment_order.name,
			"from_account": payment_order.from_account,
			"to_account": payment_order.to_account_no,
			"to_ifsc": payment_order.to_ifsc,
			"amount_paise": int(payment_order.amount * 100),  # NPCI uses paise
			"payment_rail": payment_order.payment_rail,
			"narration": payment_order.narration or "",
			"timestamp": now_datetime().isoformat()
		}

		# API call to NPCI
		if api_key and endpoint:
			headers = {
				"Content-Type": "application/json",
				"X-API-Key": api_key,
				"X-API-Secret": api_secret
			}
			response = requests.post(
				f"{endpoint}/payments/execute",
				json=payload,
				headers=headers,
				timeout=30
			)
			result = response.json()

			if response.status_code == 200 and result.get("status") == "SUCCESS":
				return {
					"status": "success",
					"utr_number": result.get("utr", f"UTR{now_datetime().strftime('%Y%m%d%H%M%S')}"),
					"settled_at": now_datetime(),
					"npci_response": result
				}
			else:
				return {
					"status": "failed",
					"error_message": result.get("message", "NPCI payment failed"),
					"npci_response": result
				}
		else:
			# Simulated success for development/testing
			return {
				"status": "simulated",
				"utr_number": f"SIMUTR{now_datetime().strftime('%Y%m%d%H%M%S')}",
				"settled_at": now_datetime(),
				"message": "NPCI API not fully configured. Simulated payment processing."
			}

	except requests.exceptions.RequestException as e:
		frappe.log_error(f"NPCI API call failed: {str(e)}", "NPCI Integration")
		return {
			"status": "failed",
			"error_message": f"NPCI connection error: {str(e)}"
		}
	except Exception as e:
		frappe.log_error(f"NPCI integration error: {str(e)}", "NPCI Integration")
		return {
			"status": "failed",
			"error_message": str(e)
		}


def verify_transaction_status(utr_number):
	"""Check settlement status of a transaction by UTR number.
	
	Args:
		utr_number: NPCI-assigned UTR number
		
	Returns:
		dict: Status details
	"""
	if not is_integration_enabled("npci"):
		return {"status": "unknown", "message": "NPCI integration not configured"}

	try:
		endpoint = get_endpoint_url("npci")
		api_key = get_api_key("npci")

		if api_key and endpoint:
			headers = {"X-API-Key": api_key}
			response = requests.get(
				f"{endpoint}/payments/status/{utr_number}",
				headers=headers,
				timeout=15
			)
			return response.json()
		else:
			return {"status": "settled", "utr": utr_number, "message": "Status simulated (no API key)"}

	except Exception as e:
		frappe.log_error(f"NPCI status check failed: {str(e)}", "NPCI Integration")
		return {"status": "error", "message": str(e)}
