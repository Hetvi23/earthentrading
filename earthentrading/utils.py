# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe


def is_earth_trading_quotation_workflow_active() -> bool:
	return bool(
		frappe.db.exists(
			"Workflow",
			{
				"document_type": "Quotation",
				"workflow_name": "Earth Trading Quotation",
				"is_active": 1,
			},
		)
	)


def is_earth_trading_sales_order_workflow_active() -> bool:
	return bool(
		frappe.db.exists(
			"Workflow",
			{
				"document_type": "Sales Order",
				"workflow_name": "Earth Trading Sales Order",
				"is_active": 1,
			},
		)
	)
