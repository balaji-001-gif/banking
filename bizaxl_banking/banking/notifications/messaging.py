# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
import requests
import json
from frappe.utils import now_datetime
from ..doctype.banking_integration_settings.banking_integration_settings import (
	is_integration_enabled, get_api_key, get_integration_settings
)

"""
SMS / Email / WhatsApp Notifications Integration Module

Handles: Transaction alerts, OTP delivery, EMI reminders, account statements
Requires: MSG91 / Twilio / AWS SNS / Exotel API credentials in Banking Integration Settings
"""


# ---------------------------------------------------------------------------
# SMS
# ---------------------------------------------------------------------------

def send_sms(mobile, message, template_name=None):
	"""Send SMS notification.
	
	Args:
		mobile: Recipient mobile number (10-digit)
		message: SMS text content
		template_name: Optional template identifier
		
	Returns:
		dict: Delivery result
	"""
	if not is_integration_enabled("sms"):
		return {"status": "disabled", "message": "SMS not configured"}

	try:
		settings = get_integration_settings()
		api_key = get_api_key("sms")
		sender_id = settings.get("sms_sender_id") or "BIZAXL"
		provider = settings.get("sms_provider") or "MSG91"
		endpoint = settings.get("sms_live_endpoint") or ""

		if api_key:
			if provider == "MSG91":
				url = endpoint or "https://api.msg91.com/api/v5/flow"
				payload = {
					"sender": sender_id,
					"mobiles": mobile,
					"message": message,
					"template_id": template_name or ""
				}
				headers = {"authkey": api_key, "Content-Type": "application/json"}
				response = requests.post(url, json=payload, headers=headers, timeout=10)
				result = response.json()
				return {"status": "sent" if response.status_code == 200 else "failed",
						"provider": provider, "response": result}
			elif provider == "Twilio":
				# Placeholder for Twilio integration
				return {"status": "simulated", "provider": "Twilio",
						"message": "Twilio integration stub. SMS logged."}
			else:
				# Generic HTTP API
				url = endpoint or "https://api.sms-provider.com/send"
				payload = {
					"api_key": api_key,
					"sender": sender_id,
					"mobile": mobile,
					"message": message
				}
				response = requests.post(url, json=payload, timeout=10)
				return {"status": "sent" if response.status_code == 200 else "failed",
						"response": response.text}
		else:
			return {"status": "simulated", "to": mobile, "message": message[:50] + "..." if len(message) > 50 else message}

	except Exception as e:
		frappe.log_error(f"SMS send error: {str(e)}", "SMS Integration")
		return {"status": "error", "error_message": str(e)}


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def send_email(to, subject, message, attachments=None):
	"""Send email notification using Frappe's built-in email or external API.
	
	Args:
		to: Recipient email address
		subject: Email subject
		message: Email body (HTML supported)
		attachments: Optional list of file paths
		
	Returns:
		dict: Delivery result
	"""
	if not is_integration_enabled("email"):
		return {"status": "disabled", "message": "Email not configured"}

	try:
		settings = get_integration_settings()
		from_address = settings.get("email_from_address") or "noreply@bizaxl.com"

		# Use Frappe's built-in email
		frappe.sendmail(
			recipients=to,
			sender=from_address,
			subject=subject,
			message=message,
			attachments=attachments or []
		)
		return {"status": "sent", "to": to, "subject": subject}

	except Exception as e:
		frappe.log_error(f"Email send error: {str(e)}", "Email Integration")
		return {"status": "error", "error_message": str(e)}


# ---------------------------------------------------------------------------
# WhatsApp
# ---------------------------------------------------------------------------

def send_whatsapp(mobile, message, template_name=None, template_params=None):
	"""Send WhatsApp message using configured provider.
	
	Args:
		mobile: Recipient mobile with country code
		message: Message content (used if no template)
		template_name: WhatsApp template name
		template_params: Template variable values
		
	Returns:
		dict: Delivery result
	"""
	if not is_integration_enabled("whatsapp"):
		return {"status": "disabled", "message": "WhatsApp not configured"}

	try:
		settings = get_integration_settings()
		api_key = settings.get("whatsapp_api_key") or ""
		business_phone = settings.get("whatsapp_business_phone") or ""

		if api_key and business_phone:
			# WhatsApp Business API (Meta) integration stub
			url = "https://graph.facebook.com/v18.0/" + business_phone + "/messages"
			payload = {
				"messaging_product": "whatsapp",
				"to": mobile,
				"type": "text",
				"text": {"body": message}
			}
			headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
			response = requests.post(url, json=payload, headers=headers, timeout=10)
			return {"status": "sent" if response.status_code == 200 else "failed",
					"provider": "WhatsApp Business"}
		else:
			return {"status": "simulated", "to": mobile, "message": message[:50]}

	except Exception as e:
		frappe.log_error(f"WhatsApp send error: {str(e)}", "WhatsApp Integration")
		return {"status": "error", "error_message": str(e)}


# ---------------------------------------------------------------------------
# Convenience: Send transaction alerts
# ---------------------------------------------------------------------------

def send_transaction_alert(customer, account, payment_order):
	"""Send multi-channel transaction alert to customer.
	
	Sends SMS, email, and WhatsApp (whichever is enabled).
	
	Args:
		customer: Banking Customer document/name
		account: Banking Account document/name
		payment_order: Banking Payment Order document
	"""
	if isinstance(customer, str):
		customer = frappe.get_doc("Banking Customer", customer)
	if isinstance(account, str):
		account = frappe.get_doc("Banking Account", account)

	mobile = getattr(customer, "mobile", None)
	# Get the customer's own email (look up from linked User or email field)
	email = getattr(customer, "email", None) or frappe.db.get_value(
		"User", {"mobile_no": customer.mobile}, "email"
	) if customer.mobile else None

	account_display = getattr(account, "account_number", None) or account.name

	message = (
		f"Transaction Alert: ₹{payment_order.amount:,.2f} debited from "
		f"account {account_display}. "
		f"UTR: {payment_order.utr_number}. "
		f"Date: {payment_order.settled_at}"
	)

	# Send via all enabled channels
	if mobile:
		send_sms(mobile, message, template_name="txn_alert")
		send_whatsapp("91" + mobile, message)

	if email:
		send_email(email, f"Transaction Alert - {account_display}", message)


def send_emi_reminder(customer, loan_account, emi_amount, due_date):
	"""Send EMI reminder notification."""
	if isinstance(customer, str):
		customer = frappe.get_doc("Banking Customer", customer)

	mobile = customer.mobile
	message = (
		f"EMI Reminder: ₹{emi_amount:,.2f} due on {due_date} "
		f"for loan {loan_account}. Please maintain sufficient balance."
	)

	if mobile:
		send_sms(mobile, message, template_name="emi_reminder")


def send_kyc_reminder(customer, days_remaining):
	"""Send KYC re-verification reminder."""
	if isinstance(customer, str):
		customer = frappe.get_doc("Banking Customer", customer)

	mobile = customer.mobile
	message = (
		f"KYC Re-verification Due: Your KYC documents will expire in "
		f"{days_remaining} days. Please submit updated documents to avoid account restrictions."
	)

	if mobile:
		send_sms(mobile, message, template_name="kyc_reminder")
