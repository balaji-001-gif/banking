# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
import requests
from ..doctype.banking_integration_settings.banking_integration_settings import (
	is_integration_enabled, get_api_key, get_api_secret, get_endpoint_url, get_integration_settings
)

"""
CIBIL / Experian / CRIF Credit Bureau Integration Module

Handles: Credit score pull, full credit report, bureau-based underwriting
Requires: Bureau API credentials configured in Banking Integration Settings
"""


def fetch_credit_score(pan_number, full_name=None, mobile=None):
	"""Fetch credit score and report from configured bureau.
	
	Args:
		pan_number: Customer PAN (10 characters)
		full_name: Optional name for verification
		mobile: Optional mobile for additional verification
		
	Returns:
		dict: Credit report with score, account history, and enquiry info
	"""
	if not is_integration_enabled("bureau"):
		return {"status": "disabled", "message": "Credit bureau not configured"}

	try:
		endpoint = get_endpoint_url("bureau")
		api_key = get_api_key("bureau")
		api_secret = get_api_secret("bureau")
		settings = get_integration_settings()

		provider = settings.get("bureau_provider") or "CIBIL"
		member_id = settings.get("bureau_member_id") or ""
		mode = settings.get("bureau_mode") or "Sandbox"

		payload = {
			"pan": pan_number.upper(),
			"name": full_name or "",
			"mobile": mobile or "",
			"member_id": member_id,
			"report_type": "full" if mode == "Live" else "score_only",
			"purpose": "05"  # Code for 'Loan' as per bureau standards
		}

		if api_key and endpoint:
			headers = {
				"Content-Type": "application/json",
				"X-API-Key": api_key,
				"X-API-Secret": api_secret
			}
			response = requests.post(f"{endpoint}/credit-report", json=payload, headers=headers, timeout=30)
			result = response.json()

			if response.status_code == 200:
				score = result.get("score", 0)
				return {
					"status": "success",
					"provider": provider,
					"score": score,
					"report": {
						"score": score,
						"score_range": result.get("score_range", "300-900"),
						"total_accounts": result.get("total_accounts", 0),
						"active_accounts": result.get("active_accounts", 0),
						"defaults": result.get("defaults", 0),
						"enquiry_count": result.get("enquiry_count", 0),
						"credit_utilization": result.get("credit_utilization", 0),
						"oldest_trade_age_months": result.get("oldest_trade_age", 0)
					},
					"raw_response": result
				}
			else:
				return {
					"status": "failed",
					"error_message": result.get("message", "Bureau fetch failed"),
					"score": 0
				}
		else:
			# Simulated for development
			score = 750  # Default good score for simulation
			return {
				"status": "simulated",
				"provider": provider,
				"score": score,
				"report": {
					"score": score,
					"score_range": "300-900",
					"total_accounts": 8,
					"active_accounts": 3,
					"defaults": 0,
					"enquiry_count": 2,
					"credit_utilization": 35,
					"oldest_trade_age_months": 48
				},
				"message": "Bureau API not configured. Simulated score: 750."
			}

	except Exception as e:
		frappe.log_error(f"Bureau fetch error for PAN {pan_number}: {str(e)}", "Bureau Integration")
		return {"status": "error", "error_message": str(e), "score": 0}


def evaluate_loan_eligibility(pan_number, requested_amount, monthly_income, existing_obligations=0):
	"""Evaluate loan eligibility using bureau data.
	
	Args:
		pan_number: Customer PAN
		requested_amount: Loan amount requested
		monthly_income: Customer's monthly income
		existing_obligations: Existing monthly EMI obligations
		
	Returns:
		dict: Eligibility assessment with max eligible amount and FOIR
	"""
	bureau_result = fetch_credit_score(pan_number)
	
	if bureau_result.get("status") in ("disabled", "error"):
		return {
			"status": "manual_review",
			"message": "Bureau unavailable. Manual underwriting required.",
			"score": 0
		}

	score = bureau_result.get("score", 0) if bureau_result.get("status") == "success" else 750
	total_obligations = existing_obligations

	# Calculate FOIR
	if monthly_income > 0:
		foir = round((total_obligations + (requested_amount * 0.02)) / monthly_income * 100, 2)
	else:
		foir = 100

	# Eligibility rules
	is_eligible = False
	if score >= 750 and foir <= 50:
		is_eligible = True
		max_eligible = min(requested_amount, monthly_income * 60 - total_obligations * 12)
	elif score >= 650 and foir <= 60:
		is_eligible = True
		max_eligible = min(requested_amount * 0.8, monthly_income * 48 - total_obligations * 12)
	else:
		max_eligible = 0

	return {
		"status": "eligible" if is_eligible else "rejected",
		"score": score,
		"foir": foir,
		"max_eligible_amount": max(0, max_eligible),
		"risk_grade": _calculate_risk_grade(score),
		"bureau_report": bureau_result.get("report", {})
	}


def _calculate_risk_grade(score):
	"""Convert bureau score to risk grade (A1-D)."""
	if score >= 800:
		return "A1"
	elif score >= 750:
		return "A2"
	elif score >= 700:
		return "B1"
	elif score >= 650:
		return "B2"
	elif score >= 550:
		return "C"
	else:
		return "D"
