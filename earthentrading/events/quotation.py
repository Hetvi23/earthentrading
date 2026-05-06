# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from earthentrading.utils import is_earth_trading_quotation_workflow_active


def before_insert(doc, method):
	if doc.amended_from:
		prev_rev = frappe.db.get_value("Quotation", doc.amended_from, "custom_et_revision_no") or 1
		doc.custom_et_revision_no = int(prev_rev) + 1
	elif not doc.get("custom_et_revision_no"):
		doc.custom_et_revision_no = 1


def validate(doc, method):
	if doc.get("opportunity") and not doc.get("custom_et_assigned_trader"):
		owner = frappe.db.get_value("Opportunity", doc.opportunity, "opportunity_owner")
		trader = frappe.db.get_value("Opportunity", doc.opportunity, "custom_et_assigned_trader")
		doc.custom_et_assigned_trader = trader or owner
	if doc.get("opportunity") and not doc.get("custom_et_deal_type"):
		dt = frappe.db.get_value("Opportunity", doc.opportunity, "custom_et_deal_type")
		if dt:
			doc.custom_et_deal_type = dt


def before_submit(doc, method):
	if not is_earth_trading_quotation_workflow_active():
		return
	ws = doc.get("workflow_state")
	if ws != "ET Quote Approved":
		frappe.throw(
			_("Quotation can only be submitted after workflow approval (current: {0}).").format(ws or _("unset"))
		)
