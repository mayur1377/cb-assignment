frappe.ui.form.on('CB PM Program', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Roll Out to Stores'), () => {
				frappe.call({
					method: 'rollout',
					doc: frm.doc,
					freeze: true,
					callback(r) {
						if (!r.exc) frm.reload_doc();
					},
				});
			}).addClass('btn-primary');
		}
	},
});
