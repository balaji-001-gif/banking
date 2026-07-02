# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingBulkPaymentEntry(Document):
	"""Child table entry for Bulk Payment — each row is one beneficiary."""
	pass
