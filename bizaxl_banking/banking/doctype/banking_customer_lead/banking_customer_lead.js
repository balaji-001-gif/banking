// Copyright (c) 2026, Bizaxl and contributors
// For license information, please see license.txt

frappe.ui.form.on('Banking Customer Lead', {
	refresh: function(frm) {
		// Add custom button to convert lead to customer
		if (!frm.doc.__islocal && frm.doc.lead_status === 'Qualified' && !frm.doc.converted_to_customer) {
			frm.add_custom_button(__('Create Customer'), function() {
				frappe.confirm(
					__('Are you sure you want to convert this Lead to a Banking Customer?'),
					function() {
						frappe.call({
							method: 'convert_to_customer',
							doc: frm.doc,
							callback: function(r) {
								if (!r.exc) {
									frappe.show_alert({
										message: __('Lead Converted Successfully!'),
										indicator: 'green'
									});
									frm.reload_doc();
									
									// Navigate to the newly created customer
									if (r.message) {
										frappe.set_route('Form', 'Banking Customer', r.message);
									}
								}
							}
						});
					}
				);
			}).addClass('btn-primary');
		}
	}
});
