# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from earthentrading.utils import (
	is_earth_trading_quotation_workflow_active,
	is_earth_trading_sales_order_workflow_active,
)


def validate(doc, method):
	_sync_assigned_trader_from_items(doc)


def before_submit(doc, method):
	if is_earth_trading_sales_order_workflow_active():
		ws = doc.get("workflow_state")
		if ws != "ET SO Approved":
			frappe.throw(
				_("Sales Order can only be submitted after workflow approval (current: {0}).").format(ws or _("unset"))
			)
	if is_earth_trading_quotation_workflow_active():
		_validate_linked_quotations_approved(doc)


def _sync_assigned_trader_from_items(doc):
	if doc.get("custom_et_assigned_trader"):
		return
	users = set()
	for row in doc.get("items") or []:
		if not row.get("quotation_item"):
			continue
		q = frappe.db.get_value("Quotation Item", row.quotation_item, "parent")
		if not q:
			continue
		trader = frappe.db.get_value("Quotation", q, "custom_et_assigned_trader")
		owner = frappe.db.get_value("Quotation", q, "owner")
		if trader:
			users.add(trader)
		elif owner:
			users.add(owner)
	if len(users) == 1:
		doc.custom_et_assigned_trader = users.pop()
	elif len(users) > 1:
		frappe.msgprint(
			_("Multiple assigned traders found on linked quotations; set Assigned Trader manually."),
			title=_("Earth Trading"),
			indicator="orange",
		)


def _validate_linked_quotations_approved(doc):
	quotations = _linked_quotation_names(doc)
	for qname in quotations:
		if frappe.db.get_value("Quotation", qname, "docstatus") != 1:
			frappe.throw(_("Linked Quotation {0} is not submitted.").format(qname))
		if not is_earth_trading_quotation_workflow_active():
			continue
		ws = frappe.db.get_value("Quotation", qname, "workflow_state")
		if ws != "ET Quote Approved":
			frappe.throw(
				_("Linked Quotation {0} must be workflow-approved before Sales Order submit (state: {1}).").format(
					qname, ws or _("unset")
				)
			)


def _linked_quotation_names(doc) -> set[str]:
	names: set[str] = set()
	for row in doc.get("items") or []:
		if not row.get("quotation_item"):
			continue
		parent = frappe.db.get_value("Quotation Item", row.quotation_item, "parent")
		if parent:
			names.add(parent)
	return names
