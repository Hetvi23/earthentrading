# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Desk workspace: Earth Trading CRM dashboard (pipeline, capture, parties, engagement)."""

import frappe

from earthentrading.setup.kanban import BOARD_NAME
from earthentrading.setup.workspace_editor import (
	reload_workspace_into_doc_for_export,
	sync_workspace_editorjs,
)


def ensure_earth_trading_workspace():
	name = "Earth Trading CRM"

	if frappe.db.exists("Workspace", name):
		ws = frappe.get_doc("Workspace", name)
	else:
		ws = frappe.new_doc("Workspace")
		ws.label = name

	ws.title = "Earth Trading CRM"
	ws.sequence_id = 4.7
	ws.public = 1
	ws.module = "Earth Ent Trading"
	ws.icon = "organization"
	ws.indicator_color = "green"
	ws.is_hidden = 0
	ws.hide_custom = 0
	ws.parent_page = ""
	ws.restrict_to_domain = ""
	ws.content = "[]"

	_shortcuts(ws)
	_links(ws)
	ws.charts = []

	ws.save(ignore_permissions=True)
	sync_workspace_editorjs(name, '<span class="h4"><b>Earth Trading CRM</b></span>')
	reload_workspace_into_doc_for_export(name)


def _shortcuts(ws):
	ws.shortcuts = []

	def sc(**kwargs):
		ws.append("shortcuts", kwargs)

	sc(
		type="DocType",
		doc_view="Kanban",
		link_to="Lead",
		label="Lead pipeline board",
		kanban_board=BOARD_NAME,
		color="Green",
		icon="organization",
	)
	sc(
		type="DocType",
		link_to="Lead",
		label="All open leads",
		color="Blue",
		format="{} open",
		stats_filter='{"status": "Open"}',
		doc_view="List",
	)
	sc(
		type="DocType",
		link_to="Lead",
		label="My leads",
		color="Orange",
		format="{} mine",
		stats_filter="{lead_owner: frappe.session.user}",
		doc_view="List",
	)
	for stage, color in (
		("Lead", "Blue"),
		("Qualified", "Cyan"),
		("Negotiation", "Pink"),
		("Won", "Green"),
		("Lost", "Red"),
	):
		sc(
			type="DocType",
			link_to="Lead",
			label=f"Stage: {stage}",
			color=color,
			format="{} ",
			stats_filter=frappe.as_json({"custom_et_sales_stage": stage}, indent=None),
			doc_view="List",
		)
	sc(
		type="DocType",
		link_to="Lead",
		label="Brokerage",
		color="Yellow",
		format="{} ",
		stats_filter='{"custom_et_deal_type": "Brokerage"}',
		doc_view="List",
	)
	sc(
		type="DocType",
		link_to="Lead",
		label="Principal",
		color="Gray",
		format="{} ",
		stats_filter='{"custom_et_deal_type": "Principal"}',
		doc_view="List",
	)

	sc(type="DocType", link_to="Opportunity", label="Opportunities", color="Purple", doc_view="List")

	sc(type="DocType", link_to="Communication", label="Communications log", doc_view="List")
	sc(type="DocType", link_to="ToDo", label="Tasks & follow-ups", doc_view="List")

	sc(type="URL", url="/earth-trading-lead", label="Public web lead form", color="Grey", icon="globe")


def _links(ws):
	ws.links = []

	def cb(label, icon=None):
		ws.append("links", {"type": "Card Break", "label": label, "icon": icon or ""})

	def ln(label, dt, onboard=0):
		ws.append(
			"links",
			{
				"type": "Link",
				"label": label,
				"link_type": "DocType",
				"link_to": dt,
				"onboard": onboard,
				"is_query_report": 0,
			},
		)

	def rep(label, report, ref_dt, onboard=0):
		ws.append(
			"links",
			{
				"type": "Link",
				"label": label,
				"link_type": "Report",
				"link_to": report,
				"dependencies": "",
				"is_query_report": 1,
				"onboard": onboard,
				**({"report_ref_doctype": ref_dt} if ref_dt else {}),
			},
		)

	cb("Lead capture & data")

	ln("New Lead", "Lead")
	ln("Data Import", "Data Import")

	cb("Parties (buyers & suppliers)")
	ln("Customer", "Customer")
	ln("Supplier", "Supplier")
	ln("Contact", "Contact")

	cb("Quotations & documents")
	ln("Quotation", "Quotation")
	ln("Sales Order", "Sales Order")

	if frappe.db.exists("DocType", "Contract"):
		ln("Contract", "Contract")

	cb("Operational checklists")
	if frappe.db.exists("DocType", "ET Task Template"):
		ln("Task templates", "ET Task Template")

	cb("Analysis (standard CRM reports)")
	if frappe.db.exists("Report", "Lead Details"):
		rep("Lead Details", "Lead Details", "Lead")
	if frappe.db.exists("Report", "Sales Pipeline Analytics"):
		rep("Sales Pipeline Analytics", "Sales Pipeline Analytics", "Opportunity")
	if frappe.db.exists("Report", "Opportunity Summary by Sales Stage"):
		rep(
			"Opportunity Summary by Sales Stage",
			"Opportunity Summary by Sales Stage",
			"Opportunity",
		)


def refresh_web_form_incoterm():
	"""Attach Incoterm to existing web forms if field was missing."""
	if not frappe.db.exists("Web Form", {"route": "earth-trading-lead"}):
		return
	wf_name = frappe.db.get_value("Web Form", {"route": "earth-trading-lead"}, "name")
	doc = frappe.get_doc("Web Form", wf_name)
	have = {r.fieldname for r in doc.web_form_fields}
	if "custom_et_incoterm" in have:
		return

	def row_dict(row):
		d = row.as_dict()
		for k in (
			"name",
			"owner",
			"creation",
			"modified",
			"modified_by",
			"docstatus",
			"parent",
			"parentfield",
			"parenttype",
			"idx",
			"doctype",
		):
			d.pop(k, None)
		return d

	field_rows = []
	for row in doc.web_form_fields:
		field_rows.append(row_dict(row))
		if row.fieldname == "custom_et_deal_type":
			field_rows.append(
				{
					"fieldname": "custom_et_incoterm",
					"label": "Incoterm",
					"fieldtype": "Link",
					"options": "Incoterm",
					"reqd": 0,
				}
			)

	doc.web_form_fields = []
	for i, row in enumerate(field_rows, start=1):
		doc.append("web_form_fields", row)
		doc.web_form_fields[-1].idx = i
	doc.save(ignore_permissions=True)
