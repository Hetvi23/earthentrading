# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Take over the standard "Selling" workspace and replace its content with
the Earth Trading sales dashboard (Trades in MT + Trades By Item charts)."""

import json
import secrets

import frappe

from earthentrading.setup.dashboard import (
	CHART_TRADES_BY_ITEM,
	CHART_TRADES_MT,
	ensure_earth_trading_dashboard,
)


WORKSPACE_NAME = "Selling"


def ensure_selling_workspace():
	ensure_earth_trading_dashboard()  # make sure the charts exist

	if frappe.db.exists("Workspace", WORKSPACE_NAME):
		ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	else:
		ws = frappe.new_doc("Workspace")
		ws.label = WORKSPACE_NAME

	ws.title = "Selling"
	ws.sequence_id = 4.6
	ws.public = 1
	ws.icon = "presentation"
	ws.indicator_color = "blue"
	ws.is_hidden = 0
	ws.hide_custom = 0
	ws.parent_page = ""
	ws.restrict_to_domain = ""

	ws.shortcuts = []
	ws.links = []
	ws.quick_lists = []

	ws.charts = []
	for chart_name in (CHART_TRADES_MT, CHART_TRADES_BY_ITEM):
		ws.append(
			"charts",
			{
				"chart_name": chart_name,
				"label": chart_name,
				"width": "Full",
			},
		)

	ws.content = _build_selling_content_json()
	ws.save(ignore_permissions=True)


def _block_id() -> str:
	return secrets.token_hex(6)


def _build_selling_content_json() -> str:
	blocks: list[dict] = []

	def push(**b):
		blocks.append(b)

	push(
		id=_block_id(),
		type="header",
		data={"text": '<span class="h4"><b>Selling</b></span>', "col": 12},
	)
	push(id=_block_id(), type="spacer", data={"col": 12})
	push(
		id=_block_id(),
		type="chart",
		data={"chart_name": CHART_TRADES_MT, "col": 12},
	)
	push(id=_block_id(), type="spacer", data={"col": 12})
	push(
		id=_block_id(),
		type="chart",
		data={"chart_name": CHART_TRADES_BY_ITEM, "col": 12},
	)

	return json.dumps(blocks)
