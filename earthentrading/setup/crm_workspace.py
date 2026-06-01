# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Desk workspace: Earth Trading CRM dashboard (pipeline, capture, parties, engagement)."""

import json
import secrets

import frappe

from earthentrading.setup.workspace_editor import (
	reload_workspace_into_doc_for_export,
)


FUNCTION_SHORTCUT_LABELS = ["Leads", "Buyers", "Sellers", "Buyer-Seller", "Broker"]
COMMODITY_SHORTCUT_LABELS = ["Pulses", "Spices", "Nuts", "Grains", "Sugar", "Feed", "Rice"]


def ensure_earth_trading_workspace():
	"""Take over the "CRM" workspace (Frappe CRM app's slot) with the trading
	tiles + inline Trade Report filter, and remove the older "Earth Trading
	CRM" workspace so only one CRM shows in the sidebar."""
	name = "CRM"

	# Clean up the previous Earth Trading CRM workspace if it still exists.
	if frappe.db.exists("Workspace", "Earth Trading CRM"):
		try:
			frappe.delete_doc("Workspace", "Earth Trading CRM", force=True, ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "earthentrading.delete_earth_trading_crm_workspace")

	if frappe.db.exists("Workspace", name):
		ws = frappe.get_doc("Workspace", name)
	else:
		ws = frappe.new_doc("Workspace")
		ws.label = name

	ws.title = "CRM"
	ws.sequence_id = 4.7
	ws.public = 1
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

	# Build a custom EditorJS layout with two clearly separated tile groups
	# (Function vs Commodity); the Trade Report widget is injected by JS.
	ws.content = _build_grouped_content_json()
	ws.save(ignore_permissions=True)

	reload_workspace_into_doc_for_export(name)


def _block_id() -> str:
	return secrets.token_hex(6)


def _build_grouped_content_json() -> str:
	blocks: list[dict] = []

	def push(**b):
		blocks.append(b)

	push(
		id=_block_id(),
		type="header",
		data={"text": '<span class="h4"><b>Earth Trading CRM</b></span>', "col": 12},
	)
	push(id=_block_id(), type="spacer", data={"col": 12})

	push(
		id=_block_id(),
		type="header",
		data={"text": '<span class="h5"><b>Leads by function</b></span>', "col": 12},
	)
	for lab in FUNCTION_SHORTCUT_LABELS:
		push(id=_block_id(), type="shortcut", data={"shortcut_name": lab, "col": 3})
	push(id=_block_id(), type="spacer", data={"col": 12})

	push(
		id=_block_id(),
		type="header",
		data={"text": '<span class="h5"><b>Leads by commodity group</b></span>', "col": 12},
	)
	for lab in COMMODITY_SHORTCUT_LABELS:
		push(id=_block_id(), type="shortcut", data={"shortcut_name": lab, "col": 3})

	# The Trade Report filter widget is mounted by trade_report_widget.js
	# directly after the last EditorJS block; it carries its own title, so
	# no anchor header here (the empty header left a visible gap).

	return json.dumps(blocks)


def _shortcuts(ws):
	ws.shortcuts = []

	def sc(**kwargs):
		ws.append("shortcuts", kwargs)

	# --- Row 1: Lead Function tiles -------------------------------------
	sc(
		type="DocType",
		link_to="Lead",
		label="Leads",
		color="Blue",
		format="{}",
		doc_view="List",
	)
	for fn, color in (
		("Buyer", "Blue"),
		("Seller", "Blue"),
		("Buyer-Seller", "Grey"),
		("Broker", "Cyan"),
	):
		# Label tweak: pluralize Buyer/Seller to match the screenshot.
		label = f"{fn}s" if fn in ("Buyer", "Seller") else fn
		sc(
			type="DocType",
			link_to="Lead",
			label=label,
			color=color,
			format="{}",
			stats_filter=frappe.as_json({"custom_et_lead_function": fn}, indent=None),
			doc_view="List",
		)

	# --- Row 2+: Commodity Group tiles -----------------------------------
	for group in ("Pulses", "Spices", "Nuts", "Grains", "Sugar", "Feed", "Rice"):
		sc(
			type="DocType",
			link_to="Lead",
			label=group,
			color="Grey",
			format="{}",
			stats_filter=frappe.as_json({"custom_et_commodity_group": group}, indent=None),
			doc_view="List",
		)

	# Trade Report filter is rendered inline on the workspace by
	# public/js/trade_report_widget.js — no shortcut needed here.


def _links(ws):
	# Workspace intentionally trimmed to the Trade Report filter only.
	ws.links = []
	ws.append(
		"links",
		{
			"type": "Link",
			"label": "Leads by Trade Report",
			"link_type": "Report",
			"link_to": "Leads by Trade Report",
			"dependencies": "",
			"is_query_report": 1,
			"onboard": 0,
			"report_ref_doctype": "Lead",
		},
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
