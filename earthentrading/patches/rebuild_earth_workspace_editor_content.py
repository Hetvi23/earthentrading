"""Rebuild Earth Trading Desk workspaces (fixes blank hub/CRM dashboards)."""

import frappe

from earthentrading.setup.crm_workspace import ensure_earth_trading_workspace
from earthentrading.setup.hub_workspace import ensure_earth_trading_hub_workspace


def execute():
	ensure_earth_trading_hub_workspace()
	ensure_earth_trading_workspace()
	frappe.db.commit()
	frappe.clear_cache()

	after_hub = (
		frappe.db.get_value("Workspace", "Earth Trading Hub", "content")
		if frappe.db.exists("Workspace", "Earth Trading Hub")
		else None
	)
	if (not after_hub or str(after_hub).strip() == "[]") and frappe.db.exists(
		"Workspace", "Earth Trading Hub"
	):
		frappe.log_error(
			"Earth Trading Hub workspace content is still empty after rebuild.",
			"earthentrading.workspace.blank",
		)
