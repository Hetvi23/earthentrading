# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Migration: legacy flat commodity/qty → ET Lead Line / Opportunity Item rows."""

from __future__ import annotations

import frappe
from frappe.utils import flt


def _delete_cf(dt: str, fieldname: str) -> None:
	name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fieldname}, "name")
	if not name:
		return
	try:
		frappe.delete_doc("Custom Field", str(name), ignore_permissions=True, force=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"earthentrading.delete_cf_{dt}_{fieldname}")


def migrate_lead_flat_fields_to_lines() -> None:
	if not frappe.db.exists("DocType", "ET Lead Line"):
		return
	if not frappe.db.has_column("Lead", "custom_et_commodity") and not frappe.db.has_column(
		"Lead", "custom_et_quantity"
	):
		return

	rows = frappe.db.sql(
		"""
		select name, IFNULL(custom_et_commodity, ''), IFNULL(custom_et_quantity, 0)
		from `tabLead`
		where IFNULL(custom_et_commodity, '') != '' OR IFNULL(custom_et_quantity, 0) != 0
		""",
		as_list=True,
	)
	for lead_name, commodity, qty in rows:
		if frappe.db.count("ET Lead Line", {"parent": lead_name}):
			continue
		lead = frappe.get_doc("Lead", lead_name)
		lead.flags.ignore_permissions = True
		q = flt(qty)
		lead.append(
			"custom_et_lines",
			{"commodity": commodity.strip() or "—", "qty": q if q else 1},
		)
		lead.save()


def migrate_opportunity_header_to_items() -> None:
	has_com = frappe.db.has_column("Opportunity", "custom_et_commodity")
	has_qty = frappe.db.has_column("Opportunity", "custom_et_quantity")
	if not has_com and not has_qty:
		return

	rows = frappe.db.sql(
		"""
		select name, IFNULL(custom_et_commodity, ''), IFNULL(custom_et_quantity, 0)
		from `tabOpportunity`
		where IFNULL(custom_et_commodity, '') != '' OR IFNULL(custom_et_quantity, 0) != 0
		""",
		as_list=True,
	)
	for oname, commodity, qty in rows:
		if frappe.db.count("Opportunity Item", filters={"parent": oname}):
			continue
		com = commodity.strip()
		q = flt(qty)
		if not com and not q:
			continue
		opp = frappe.get_doc("Opportunity", oname)
		opp.flags.ignore_permissions = True
		opp.append(
			"items",
			{
				"item_name": com or "Commodity",
				"qty": q if q else 1,
				"rate": 0,
			},
		)
		opp.save()


def remove_obsolete_trading_custom_fields() -> None:
	if frappe.db.exists("DocType", "ET Lead Line"):
		for fn in ("custom_et_commodity", "custom_et_quantity"):
			_delete_cf("Lead", fn)
	for fn in ("custom_et_commodity", "custom_et_quantity"):
		_delete_cf("Opportunity", fn)


def run_all() -> None:
	migrate_lead_flat_fields_to_lines()
	migrate_opportunity_header_to_items()
	remove_obsolete_trading_custom_fields()
