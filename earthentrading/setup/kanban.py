# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe


BOARD_NAME = "ET Lead Pipeline"


def ensure_lead_pipeline_kanban():
	if frappe.db.exists("Kanban Board", BOARD_NAME):
		return
	if not frappe.db.exists("DocType", "Lead"):
		return

	doc = frappe.get_doc(
		{
			"doctype": "Kanban Board",
			"kanban_board_name": BOARD_NAME,
			"reference_doctype": "Lead",
			"field_name": "custom_et_sales_stage",
			"private": 0,
			"show_labels": 1,
			"owner": "Administrator",
			"columns": [
				{"column_name": "Lead", "status": "Active", "indicator": "Blue"},
				{"column_name": "Qualified", "status": "Active", "indicator": "Cyan"},
				{"column_name": "Negotiation", "status": "Active", "indicator": "Orange"},
				{"column_name": "Won", "status": "Active", "indicator": "Green"},
				{"column_name": "Lost", "status": "Active", "indicator": "Red"},
			],
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
