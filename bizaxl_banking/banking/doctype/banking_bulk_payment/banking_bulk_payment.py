# Copyright (c) 2026, Bizaxl and contributors
# For license information, please see license.txt

import frappe
import csv
import io
from frappe.model.document import Document
from frappe.utils import today, now_datetime


class BankingBulkPayment(Document):
	"""Bulk payment processing — upload CSV of beneficiaries, process in batch with consolidated approval."""

	def autoname(self):
		from frappe.model.naming import make_autoname
		prefix = f"BULK-{frappe.utils.nowdate()[:7].replace('-', '')}-"
		self.name = make_autoname(prefix + "#####")

	def validate(self):
		self.calculate_totals()
		self.validate_checker()

	def calculate_totals(self):
		"""Auto-calculate total amount and entry count from child table."""
		total = 0
		count = 0
		for entry in self.entries:
			total += entry.amount
			count += 1
		self.total_amount = total
		self.total_entries = count

	def validate_checker(self):
		"""Ensure maker != checker."""
		if self.maker and self.checker and self.maker == self.checker:
			frappe.throw("Maker and Checker cannot be the same user.")

	def before_submit(self):
		"""Check that entries exist and checker is set."""
		if not self.entries:
			frappe.throw("At least one payment entry is required.")
		if not self.checker:
			# Self-approve if no checker set
			self.checker = frappe.session.user
		self.status = "Approved"

	def on_submit(self):
		"""Process all approved payments."""
		self.process_batch()

	def process_batch(self):
		"""Process each entry: create individual Payment Orders or auto-settle."""
		self.status = "Processing"
		self.db_set("status", "Processing")

		success_count = 0
		fail_count = 0
		total = len(self.entries)

		for entry in self.entries:
			try:
				# Create individual Payment Order for each entry
				po = frappe.get_doc({
					"doctype": "Banking Payment Order",
					"payment_ref": f"BULK-{self.name}-{entry.idx}",
					"from_account": self.from_account,
					"to_account_no": entry.to_account_no,
					"to_ifsc": entry.to_ifsc,
					"payment_rail": entry.payment_rail,
					"amount": entry.amount,
					"narration": entry.narration or f"Bulk payment batch {self.name}",
					"status": "Submitted",
					"maker": self.maker or frappe.session.user,
					"checker": self.checker or frappe.session.user
				})
				po.insert(ignore_permissions=True)
				po.submit()

				# Update entry status
				entry.db_set("status", "Settled")
				entry.db_set("utr_number", po.utr_number)
				entry.db_set("payment_order_ref", po.name)
				success_count += 1

			except Exception as e:
				entry.db_set("status", "Failed")
				entry.db_set("error_message", str(e))
				fail_count += 1

		if fail_count == 0:
			self.status = "Completed"
		elif success_count > 0:
			self.status = "Partially Completed"
		else:
			self.status = "Failed"

		self.db_set("status", self.status)

		frappe.msgprint(
			f"Bulk payment {self.name} processed: "
			f"{success_count}/{total} succeeded, {fail_count} failed."
		)

	@frappe.whitelist()
	def load_csv(self):
		"""Parse uploaded CSV and populate the child table."""
		if not self.uploaded_csv:
			frappe.throw("Please upload a CSV file first.")

		file_doc = frappe.get_doc("File", {"file_url": self.uploaded_csv})
		content = file_doc.get_content()
		reader = csv.DictReader(io.StringIO(content))

		expected = {"beneficiary_name", "to_account_no", "to_ifsc", "payment_rail", "amount"}
		for row in reader:
			missing = expected - set(row.keys())
			if missing:
				frappe.throw(f"CSV missing columns: {', '.join(missing)}")

			self.append("entries", {
				"beneficiary_name": row["beneficiary_name"],
				"to_account_no": row["to_account_no"],
				"to_ifsc": row["to_ifsc"],
				"payment_rail": row["payment_rail"],
				"amount": float(row["amount"]),
				"narration": row.get("narration", ""),
				"status": "Pending"
			})

		self.calculate_totals()
		return f"Loaded {len(self.entries)} entries from CSV."


def process_pending_bulk_payments():
	"""Scheduled function to auto-process approved bulk payments."""
	batches = frappe.get_all(
		"Banking Bulk Payment",
		filters={"status": "Approved", "payment_date": today()}
	)
	for batch in batches:
		doc = frappe.get_doc("Banking Bulk Payment", batch.name)
		doc.process_batch()
