# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe
from frappe.utils import flt


def validate(doc, method):
	if doc.get("custom_et_assigned_trader") and doc.custom_et_assigned_trader != doc.opportunity_owner:
		doc.opportunity_owner = doc.custom_et_assigned_trader
	elif doc.get("opportunity_owner") and not doc.get("custom_et_assigned_trader"):
		doc.custom_et_assigned_trader = doc.opportunity_owner


def _items_nonempty(doc) -> bool:
	for r in doc.get("items") or []:
		if r.get("item_code") or (r.get("item_name") or "").strip() or flt(r.get("qty")):
			return True
	return False


def _opp_item_from_lead_line(row) -> dict:
	d = row.as_dict() if hasattr(row, "as_dict") else row
	qty = flt(d.get("qty")) or 1
	out: dict = {"qty": qty, "rate": 0}
	if d.get("item_code"):
		out["item_code"] = d["item_code"]
		item_name = frappe.db.get_value("Item", d["item_code"], "item_name")
		if item_name:
			out["item_name"] = item_name
		if d.get("uom"):
			out["uom"] = d["uom"]
		else:
			su = frappe.db.get_value("Item", d["item_code"], "stock_uom")
			if su:
				out["uom"] = su
		spec = (d.get("commodity") or "").strip()
		if spec:
			out["description"] = spec
	else:
		out["item_name"] = (d.get("commodity") or "").strip() or "Commodity"
		if d.get("uom"):
			out["uom"] = d["uom"]
	return out


def before_insert(doc, method):
	"""When creating from Lead, copy trading fields and line items if present."""
	if doc.get("opportunity_from") != "Lead" or not doc.get("party_name"):
		return
	try:
		lead = frappe.get_doc("Lead", doc.party_name)
	except frappe.DoesNotExistError:
		return

	if lead.get("custom_et_deal_type") and not doc.get("custom_et_deal_type"):
		doc.custom_et_deal_type = lead.custom_et_deal_type
	if lead.get("custom_et_assigned_trader"):
		doc.custom_et_assigned_trader = lead.custom_et_assigned_trader
		doc.opportunity_owner = lead.custom_et_assigned_trader
	elif lead.get("lead_owner"):
		doc.opportunity_owner = lead.lead_owner
		doc.custom_et_assigned_trader = lead.lead_owner

	if _items_nonempty(doc):
		return
	for row in getattr(lead, "custom_et_lines", None) or []:
		doc.append("items", _opp_item_from_lead_line(row))
