frappe.listview_settings['Auto Reconcile'] = {
	add_fields: ["status"],
	get_indicator: function(doc) {
		var colors = {
			'Queued': 'orange',
			'Completed': 'green',
			'Partially Reconciled': 'orange',
			'Running': 'blue',
			'Failed': 'red',
		};
		let status = doc.status;
		return [__(status), colors[status], 'status,=,'+status];
	},
};
