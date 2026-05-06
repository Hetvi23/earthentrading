# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Unified desk workspace: CRM + projects side by side (hub)."""

import json

import frappe

from earthentrading.setup.kanban import BOARD_NAME
from earthentrading.setup.workspace_editor import (
	reload_workspace_into_doc_for_export,
	sync_workspace_editorjs,
)


HUB_NAME = "Earth Trading Hub"


def ensure_earth_trading_hub_workspace():
	"""One place to open leads, pipeline, projects, and tasks (Frappe desk workspace)."""
	if not frappe.db.exists("Workspace", HUB_NAME):
		ws = frappe.new_doc("Workspace")
		ws.label = HUB_NAME
	else:
		ws = frappe.get_doc("Workspace", HUB_NAME)

	ws.title = HUB_NAME
	ws.sequence_id = 4.5
	ws.public = 1
	ws.module = "Earth Ent Trading"
	ws.icon = "project"
	ws.indicator_color = "blue"
	ws.is_hidden = 0
	ws.hide_custom = 0
	ws.parent_page = ""
	ws.restrict_to_domain = ""
	ws.content = "[]"
	ws.charts = []

	_quick_lists(ws)
	_shortcuts(ws)
	_links(ws)

	ws.save(ignore_permissions=True)

	header = (
		'<span class="h4"><b>Earth Trading Hub</b></span>'
		'<p class="text-muted mb-0">Leads, opportunities, and delivery projects in one view. '
		'Deeper CRM lists and cards stay under <b>Earth Trading CRM</b>.</p>'
	)
	sync_workspace_editorjs(HUB_NAME, header)
	reload_workspace_into_doc_for_export(HUB_NAME)


def _quick_lists(ws):
	ws.quick_lists = []

	def ql(label: str, doctype: str, filters):
		ws.append(
			"quick_lists",
			{
				"document_type": doctype,
				"label": label,
				"quick_list_filter": json.dumps(filters, default=str),
			},
		)

	ql("Open leads", "Lead", [["status", "=", "Open"]])
	ql(
		"Active projects",
		"Project",
		[["status", "=", "Open"]],
	)
	ql(
		"Open project tasks",
		"Task",
		[
			["status", "in", ["Open", "Working", "Pending Review"]],
			["project", "is", "set"],
		],
	)


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
		label="Open leads counter",
		color="Blue",
		format="{} open",
		stats_filter='{"status": "Open"}',
		doc_view="List",
	)
	sc(type="DocType", link_to="Opportunity", label="Opportunities", color="Purple", doc_view="List")
	sc(type="DocType", link_to="Project", label="Projects", color="Cyan", doc_view="List")
	sc(type="DocType", link_to="Task", label="Project tasks", color="Pink", doc_view="List")

	sc(type="DocType", link_to="ToDo", label="My todos", doc_view="List")

	sc(type="URL", url="/app/earth-trading-crm", label="Trading CRM workspace", color="Grey")
	sc(type="URL", url="/earth-trading-lead", label="Public web lead form", color="Yellow", icon="globe")


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

	cb("Leads & sales")
	ln("New Lead", "Lead")
	ln("Data Import", "Data Import")
	if frappe.db.exists("DocType", "Customer"):
		ln("Customers", "Customer")

	cb("Delivery & templates")
	if frappe.db.exists("DocType", "Project"):
		ln("New Project", "Project")
	ln("Project Template", "Project Template")
	if frappe.db.exists("DocType", "ET Task Template"):
		ln("ET checklist templates", "ET Task Template")

	cb("Documents")
	if frappe.db.exists("DocType", "Quotation"):
		ln("Quotation", "Quotation")
	if frappe.db.exists("DocType", "Sales Order"):
		ln("Sales Order", "Sales Order")

	cb("Reports")
	if frappe.db.exists("Report", "Lead Details"):
		rep("Lead Details", "Lead Details", "Lead")
	if frappe.db.exists("Report", "Sales Pipeline Analytics"):
		rep("Sales Pipeline Analytics", "Sales Pipeline Analytics", "Opportunity")
