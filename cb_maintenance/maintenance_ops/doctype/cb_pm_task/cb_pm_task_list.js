frappe.listview_settings['CB PM Task'] = {
	add_fields: ['status', 'outlet', 'due_date', 'result', 'linked_ticket'],

	get_indicator(doc) {
		const map = {
			'Scheduled': ['Scheduled', 'blue',   'status,=,Scheduled'],
			'Due':       ['Due',       'orange', 'status,=,Due'],
			'Overdue':   ['Overdue',   'red',    'status,=,Overdue'],
			'Completed': ['Completed', 'green',  'status,=,Completed'],
			'Failed':    ['Failed',    'red',    'status,=,Failed'],
		};
		return map[doc.status] || [doc.status, 'grey', 'status,=,' + doc.status];
	},

	formatters: {
		due_date(value, field, doc) {
			if (!value) return '';
			const due = frappe.datetime.str_to_obj(value);
			const today = frappe.datetime.str_to_obj(frappe.datetime.nowdate());
			if (doc.status === 'Overdue' || due < today) {
				return `<span style="color: #C8102E; font-weight: 600;">${frappe.datetime.str_to_user(value)}</span>`;
			}
			if (doc.status === 'Due') {
				return `<span style="color: #F4821F; font-weight: 600;">${frappe.datetime.str_to_user(value)}</span>`;
			}
			return frappe.datetime.str_to_user(value);
		},
		linked_ticket(value) {
			if (!value) return '';
			return `<a href="/app/cb-maintenance-ticket/${value}" onclick="event.stopPropagation()">🎫 ${value}</a>`;
		},
	},
};
