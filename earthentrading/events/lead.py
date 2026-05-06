# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

SALES_STAGES = ("Lead", "Qualified", "Negotiation", "Won", "Lost")


def _stage_index(stage: str | None) -> int:
	s = stage or "Lead"
	if s not in SALES_STAGES:
		frappe.throw(_("Invalid Sales Stage {0}").format(s))
	return SALES_STAGES.index(s)


def validate_sales_stage_transition(doc, old_stage: str | None, new_stage: str | None):
	if old_stage == new_stage:
		return
	if not new_stage:
		return
	old = old_stage or "Lead"
	new = new_stage
	if old == "Won" and new != "Won":
		frappe.throw(_("Cannot change Sales Stage after Won."))
	if old == "Lost" and new != "Lost":
		frappe.throw(_("Cannot change Sales Stage after Lost."))
	if new == "Lost":
		return
	if new == "Won":
		if old != "Negotiation":
			frappe.throw(_("You can only set Won from Negotiation."))
		return
	old_i = _stage_index(old)
	new_i = _stage_index(new)
	if new_i < old_i:
		frappe.throw(_("Sales Stage cannot move backwards ({0} → {1}).").format(old, new))
	if new_i > old_i + 1:
		frappe.throw(_("Sales Stage cannot skip a step ({0} → {1}).").format(old, new))


def validate(doc, method):
	if doc.is_new():
		return
	old = doc.get_doc_before_save()
	if not old:
		return
	old_stage = old.get("custom_et_sales_stage") or "Lead"
	new_stage = doc.get("custom_et_sales_stage") or "Lead"
	validate_sales_stage_transition(doc, old_stage, new_stage)


def before_save(doc, method):
	"""Keep Lead Owner and Assigned Trader aligned."""
	if doc.get("custom_et_assigned_trader") and doc.custom_et_assigned_trader != doc.lead_owner:
		doc.lead_owner = doc.custom_et_assigned_trader
	elif doc.get("lead_owner") and not doc.get("custom_et_assigned_trader"):
		doc.custom_et_assigned_trader = doc.lead_owner
