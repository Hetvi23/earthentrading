# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Custom fields for Lead, Opportunity, Quotation, Sales Order, Project."""

CUSTOM_FIELDS = {
	"Lead": [
		{
			"fieldname": "custom_et_trading_section",
			"fieldtype": "Section Break",
			"label": "Trading details",
			"insert_after": "status",
			"collapsible": 1,
		},
		{
			"fieldname": "custom_et_sales_stage",
			"fieldtype": "Select",
			"label": "Sales Stage",
			"options": "Lead\nQualified\nNegotiation\nWon\nLost",
			"default": "Lead",
			"insert_after": "custom_et_trading_section",
			"in_list_view": 1,
			"in_standard_filter": 1,
		},
		{
			"fieldname": "custom_et_assigned_trader",
			"fieldtype": "Link",
			"options": "User",
			"label": "Assigned Trader",
			"insert_after": "custom_et_sales_stage",
		},
		{
			"fieldname": "custom_et_region",
			"fieldtype": "Data",
			"label": "Region",
			"insert_after": "custom_et_assigned_trader",
		},
		{
			"fieldname": "custom_et_commodities_section",
			"fieldtype": "Section Break",
			"label": "Commodities & quantities",
			"insert_after": "custom_et_region",
		},
		{
			"fieldname": "custom_et_lines",
			"fieldtype": "Table",
			"label": "Lines",
			"options": "ET Lead Line",
			"insert_after": "custom_et_commodities_section",
			"allow_on_submit": 0,
		},
		{
			"fieldname": "custom_et_deal_type",
			"fieldtype": "Select",
			"label": "Deal Type",
			"options": "\nBrokerage\nPrincipal",
			"insert_after": "custom_et_lines",
			"in_standard_filter": 1,
		},
		{
			"fieldname": "custom_et_incoterm",
			"fieldtype": "Link",
			"options": "Incoterm",
			"label": "Incoterm",
			"insert_after": "custom_et_deal_type",
		},
	],
	"Opportunity": [
		{
			"fieldname": "custom_et_trading_section",
			"fieldtype": "Section Break",
			"label": "Trading details",
			"insert_after": "territory",
			"collapsible": 1,
		},
		{
			"fieldname": "custom_et_assigned_trader",
			"fieldtype": "Link",
			"options": "User",
			"label": "Assigned Trader",
			"insert_after": "custom_et_trading_section",
		},
		{
			"fieldname": "custom_et_deal_type",
			"fieldtype": "Select",
			"label": "Deal Type",
			"options": "\nBrokerage\nPrincipal",
			"insert_after": "custom_et_assigned_trader",
		},
	],
	"Customer": [
		{
			"fieldname": "custom_et_party_section",
			"fieldtype": "Section Break",
			"label": "Group & hierarchy",
			"insert_after": "territory",
			"collapsible": 1,
		},
		{
			"fieldname": "custom_et_parent_customer",
			"fieldtype": "Link",
			"options": "Customer",
			"label": "Parent company",
			"description": "Associated / parent buyer in a group structure",
			"insert_after": "custom_et_party_section",
		},
	],
	"Supplier": [
		{
			"fieldname": "custom_et_party_section",
			"fieldtype": "Section Break",
			"label": "Group & hierarchy",
			"insert_after": "supplier_group",
			"collapsible": 1,
		},
		{
			"fieldname": "custom_et_parent_supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"label": "Parent company",
			"description": "Associated / parent supplier in a group structure",
			"insert_after": "custom_et_party_section",
		},
	],
	"Quotation": [
		{
			"fieldname": "custom_et_trading_section",
			"fieldtype": "Section Break",
			"label": "Trading details",
			"insert_after": "incoterm",
			"collapsible": 1,
		},
		{
			"fieldname": "custom_et_assigned_trader",
			"fieldtype": "Link",
			"options": "User",
			"label": "Assigned Trader",
			"insert_after": "custom_et_trading_section",
		},
		{
			"fieldname": "custom_et_deal_type",
			"fieldtype": "Select",
			"label": "Deal Type",
			"options": "\nBrokerage\nPrincipal",
			"insert_after": "custom_et_assigned_trader",
		},
		{
			"fieldname": "custom_et_revision_no",
			"fieldtype": "Int",
			"label": "Revision No",
			"default": "1",
			"read_only": 1,
			"no_copy": 0,
			"insert_after": "custom_et_deal_type",
		},
	],
	"Sales Order": [
		{
			"fieldname": "custom_et_trading_section",
			"fieldtype": "Section Break",
			"label": "Trading details",
			"insert_after": "incoterm",
			"collapsible": 1,
		},
		{
			"fieldname": "custom_et_assigned_trader",
			"fieldtype": "Link",
			"options": "User",
			"label": "Assigned Trader",
			"insert_after": "custom_et_trading_section",
		},
		{
			"fieldname": "custom_et_deal_type",
			"fieldtype": "Select",
			"label": "Deal Type",
			"options": "\nBrokerage\nPrincipal",
			"insert_after": "custom_et_assigned_trader",
		},
	],
	"Project": [
		{
			"fieldname": "custom_et_checklist_section",
			"fieldtype": "Section Break",
			"label": "Earth Trading checklist",
			"description": (
				"Pick an ET Task Template once per project to create Tasks and assign them to the project team "
				"(or to the assignee chosen on each template line)."
			),
			"insert_after": "project_template",
			"collapsible": 1,
		},
		{
			"fieldname": "custom_et_task_template",
			"fieldtype": "Link",
			"label": "ET Task Template",
			"options": "ET Task Template",
			"insert_after": "custom_et_checklist_section",
		},
		{
			"fieldname": "custom_et_checklist_spawned",
			"fieldtype": "Check",
			"label": "Checklist tasks created",
			"read_only": 1,
			"default": "0",
			"insert_after": "custom_et_task_template",
			"description": "Set automatically after tasks are created from the template (runs once per project).",
		},
	],
}
