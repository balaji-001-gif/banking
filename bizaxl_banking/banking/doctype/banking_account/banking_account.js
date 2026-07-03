// Copyright (c) 2026, Bizaxl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Banking Account', {
	refresh: function(frm) {
		// Button to Transfer Funds (Create Payment Order)
		if (frm.doc.docstatus === 1 && frm.doc.account_status === 'Active') {
			frm.add_custom_button(__('Transfer Funds'), function() {
				frappe.new_doc('Banking Payment Order', {
					'from_account': frm.doc.name
				});
			}, __('Actions'));

			// Button to Create NACH Mandate
			frm.add_custom_button(__('Create Mandate'), function() {
				frappe.new_doc('Banking NACH Mandate', {
					'account': frm.doc.name
				});
			}, __('Actions'));
		}
	}
});
