// Copyright (c) 2026, Bizaxl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Banking Customer', {
	refresh: function(frm) {
		// Button to create a new Account
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Create Account'), function() {
				frappe.new_doc('Banking Account', {
					'customer': frm.doc.name,
					'branch': frm.doc.branch
				});
			}, __('Create'));

			// Button to create a new Loan Application
			frm.add_custom_button(__('Create Loan Application'), function() {
				frappe.new_doc('Banking Loan Application', {
					'applicant': frm.doc.name
				});
			}, __('Create'));
		}
	}
});
