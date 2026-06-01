# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Earth Trading dashboard — Trades in MT (time series) and Trades By Item.

Charts source from Sales Order / Sales Order Item (qty is in MT in this app's
convention — see Sales Order Item.uom defaulting to Metric Ton). User-facing
filter labels mirror the Trade Report columns (Commodity / Origin /
Destination / Contract Type-as-Role) so the dashboard feels consistent with
the Trade Report table on Lead.
"""

import json

import frappe

DASHBOARD_NAME = "Earth Trading Trades"
MODULE = "Earth Ent Trading"

CHART_TRADES_MT = "Earth Trading - Trades in MT"
CHART_TRADES_BY_ITEM = "Earth Trading - Trades By Item"


def _chart_defs():
	return [
		{
			"chart_name": CHART_TRADES_MT,
			"chart_type": "Sum",
			"document_type": "Sales Order Item",
			"parent_document_type": "Sales Order",
			"based_on": "delivery_date",
			"value_based_on": "qty",
			"timeseries": 1,
			"type": "Bar",
			"time_interval": "Yearly",
			"timespan": "Last Year",
			"is_public": 1,
			"module": MODULE,
			"filters_json": json.dumps(
				[
					["Sales Order Item", "docstatus", "=", 1],
				]
			),
		},
		{
			"chart_name": CHART_TRADES_BY_ITEM,
			"chart_type": "Group By",
			"document_type": "Sales Order Item",
			"parent_document_type": "Sales Order",
			"group_by_type": "Sum",
			"group_by_based_on": "item_name",
			"aggregate_function_based_on": "qty",
			"type": "Bar",
			"timespan": "Last Year",
			"is_public": 1,
			"module": MODULE,
			"number_of_groups": 10,
			"filters_json": json.dumps(
				[
					["Sales Order Item", "docstatus", "=", 1],
				]
			),
		},
	]


def ensure_earth_trading_dashboard():
	if not frappe.db.exists("DocType", "Dashboard Chart"):
		return

	for spec in _chart_defs():
		name = spec["chart_name"]
		if frappe.db.exists("Dashboard Chart", name):
			doc = frappe.get_doc("Dashboard Chart", name)
			for k, v in spec.items():
				if k == "chart_name":
					continue
				setattr(doc, k, v)
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc({"doctype": "Dashboard Chart", **spec})
			doc.insert(ignore_permissions=True)

	if frappe.db.exists("Dashboard", DASHBOARD_NAME):
		dash = frappe.get_doc("Dashboard", DASHBOARD_NAME)
		dash.charts = []
	else:
		dash = frappe.new_doc("Dashboard")
		dash.dashboard_name = DASHBOARD_NAME
		dash.is_default = 0
		dash.is_standard = 0
		dash.module = MODULE

	for spec in _chart_defs():
		dash.append(
			"charts",
			{
				"chart": spec["chart_name"],
				"width": "Half",
			},
		)

	if dash.is_new():
		dash.insert(ignore_permissions=True)
	else:
		dash.save(ignore_permissions=True)

	frappe.db.commit()
