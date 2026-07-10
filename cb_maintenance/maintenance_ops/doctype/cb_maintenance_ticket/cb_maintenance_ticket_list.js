frappe.listview_settings['CB Maintenance Ticket'] = {
	add_fields: ['status', 'outlet', 'assigned_to', 'priority', 'source'],

	get_indicator(doc) {
		const map = {
			'Open':        ['Open',        'orange', 'status,=,Open'],
			'In Progress': ['In Progress', 'blue',   'status,=,In Progress'],
			'Resolved':    ['Resolved',    'green',  'status,=,Resolved'],
			'Closed':      ['Closed',      'grey',   'status,=,Closed'],
		};
		return map[doc.status] || [doc.status, 'grey', 'status,=,' + doc.status];
	},

	formatters: {
		priority(value) {
			const colors = { Urgent: 'red', High: 'orange', Medium: 'blue', Low: 'grey' };
			const color = colors[value] || 'grey';
			return `<span class="indicator-pill ${color}">${value || ''}</span>`;
		},
		source(value) {
			if (value === 'PM Failure') {
				return `<span class="indicator-pill red">${value}</span>`;
			}
			return value || '';
		},
	},

	onload(listview) {
		// Hint users about the Kanban view on first load
		if (!localStorage.getItem('cb_ticket_kanban_hint_shown')) {
			frappe.show_alert({
				message: __('💡 Tip: Switch to <b>Kanban view</b> (top-right view switcher) to drag tickets across statuses.'),
				indicator: 'blue',
			}, 8);
			localStorage.setItem('cb_ticket_kanban_hint_shown', '1');
		}
	},
};
