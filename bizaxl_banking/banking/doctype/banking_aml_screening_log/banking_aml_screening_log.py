# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BankingAmlScreeningLog(Document):
	"""Controller for Banking AML Screening Log."""
	
	def validate(self):
		self.validate_match_disposition()

	def validate_match_disposition(self):
		"""If match found, disposition must not be 'Clear'."""
		if self.match_found and self.disposition == "Clear":
			frappe.throw("Disposition cannot be 'Clear' when a match is found.")
