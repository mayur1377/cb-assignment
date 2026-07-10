frappe.ui.form.on('CB Maintenance Ticket', {
	outlet(frm) {
		frm.set_query('store_asset', () => ({
			filters: { outlet: frm.doc.outlet },
		}));
		if (!frm.doc.outlet) frm.set_value('store_asset', null);
	},
	store_asset(frm) {
		if (frm.doc.store_asset && !frm.doc.outlet) {
			frappe.db.get_value('CB Store Asset', frm.doc.store_asset, 'outlet').then((r) => {
				if (r.message) frm.set_value('outlet', r.message);
			});
		}
	},
	issue_type(frm) {
		if (!frm.doc.issue_type) return;
		frappe.db.get_value('CB Issue Type', frm.doc.issue_type, ['category', 'sub_category_1']).then((r) => {
			const values = r.message || {};
			const needle = values.sub_category_1 || values.category;
			if (!needle) return;
			frappe.db.get_list('CB Spare Part', {
				filters: [['part_name', 'like', `%${needle}%`]],
				limit: 1,
			}).then((parts) => {
				if (parts.length) frm.set_value('spare_part', parts[0].name);
			});
		});
	},
});
