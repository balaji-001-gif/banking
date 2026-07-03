// Copyright (c) 2026, Bizaxl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Banking Customer', {
	refresh: function(frm) {
		// Button to create a new Account
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__('Create Account'), function() {
				frappe.route_options = {
					'customer': frm.doc.name,
					'branch': frm.doc.branch
				};
				frappe.set_route('Form', 'Banking Account', 'New Banking Account 1');
			}, __('Create'));

			// Button to create a new Loan Application
			frm.add_custom_button(__('Create Loan Application'), function() {
				frappe.route_options = {
					'applicant': frm.doc.name
				};
				frappe.set_route('Form', 'Banking Loan Application', 'New Banking Loan Application 1');
			}, __('Create'));
		}
	}
});
