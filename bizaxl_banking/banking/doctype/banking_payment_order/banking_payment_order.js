// Copyright (c) 2026, Bizaxl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Banking Payment Order', {
	refresh: function(frm) {
		// Button to Raise Dispute Case
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Raise Dispute Case'), function() {
				// We need the customer name from the from_account
				frappe.db.get_value('Banking Account', frm.doc.from_account, 'customer', function(r) {
					frappe.route_options = {
						'linked_transaction': frm.doc.name,
						'customer': r.customer ? r.customer : ''
					};
					frappe.set_route('Form', 'Banking Dispute Case', 'New Banking Dispute Case 1');
				});
			}, __('Actions'));
		}
	}
});
