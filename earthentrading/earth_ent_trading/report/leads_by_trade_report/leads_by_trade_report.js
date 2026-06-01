// Filter sidebar for the "Leads by Trade Report" script report.
// All filters are AND'd against the Trade Report child rows.

frappe.query_reports["Leads by Trade Report"] = {
	filters: [
		{
			fieldname: "commodity",
			label: __("Commodity (contains)"),
			fieldtype: "Data",
		},
		{
			fieldname: "origin",
			label: __("Origin"),
			fieldtype: "Link",
			options: "Country",
		},
		{
			fieldname: "destination",
			label: __("Destination"),
			fieldtype: "Link",
			options: "Country",
		},
		{
			fieldname: "role",
			label: __("Role"),
			fieldtype: "Select",
			options: ["", "Seller", "Buyer", "Broker"].join("\n"),
		},
		{
			fieldname: "lead_function",
			label: __("Lead Function"),
			fieldtype: "Link",
			options: "ET Lead Function",
		},
		{
			fieldname: "commodity_group",
			label: __("Commodity Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Open", "Lead", "Converted"].join("\n"),
		},
	],
};
