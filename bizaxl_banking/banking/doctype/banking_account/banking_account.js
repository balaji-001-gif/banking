// Copyright (c) 2026, Bizaxl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Banking Account', {
	refresh: function(frm) {
		// Button to Transfer Funds (Create Payment Order)
		if (frm.doc.docstatus === 1 && frm.doc.account_status === 'Active') {
			frm.add_custom_button(__('Transfer Funds'), function() {
				frappe.route_options = {
					'from_account': frm.doc.name
				};
				frappe.set_route('Form', 'Banking Payment Order', 'New Banking Payment Order 1');
			}, __('Actions'));

			// Button to Create NACH Mandate
			frm.add_custom_button(__('Create Mandate'), function() {
				frappe.route_options = {
					'account': frm.doc.name
				};
				frappe.set_route('Form', 'Banking NACH Mandate', 'New Banking NACH Mandate 1');
			}, __('Actions'));
		}
	}
});
