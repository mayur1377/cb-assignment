frappe.ui.form.on('CB PM Task', {
	refresh(frm) {
		if (frm.doc.linked_ticket) {
			frm.add_custom_button(__('Open Ticket'), () => {
				frappe.set_route('Form', 'CB Maintenance Ticket', frm.doc.linked_ticket);
			});
		}
	},
});
