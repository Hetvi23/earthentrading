# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from earthentrading.utils import (
	is_earth_trading_quotation_workflow_active,
	is_earth_trading_sales_order_workflow_active,
)

# States that mean the SO has cleared approval. before_submit lets any of
# these through (only "Pending Assignment" actually flips docstatus=1 the
# first time, but a doc could land in In Progress / Raise Invoice / etc.
# from later transitions).
POST_APPROVAL_STATES = {
	"ET SO Pending Assignment",
	"ET SO In Progress",
	"ET SO Raise Invoice",
	"ET SO Completed",
	"ET SO Claim",
}


def validate(doc, method):
	_sync_assigned_trader_from_items(doc)
	_send_email_on_final_approval(doc)


def before_submit(doc, method):
	if is_earth_trading_sales_order_workflow_active():
		ws = doc.get("workflow_state")
		if ws not in POST_APPROVAL_STATES:
			frappe.throw(
				_(
					"Sales Order can only be submitted after workflow approval "
					"(current: {0})."
				).format(ws or _("unset"))
			)
	if is_earth_trading_quotation_workflow_active():
		_validate_linked_quotations_approved(doc)


def _send_email_on_final_approval(doc):
	"""Stub: fire a placeholder email when the SO transitions from Final
	Review to Pending Assignment (i.e. trade manager just approved). Real
	buyer/seller email templates will be wired in once provided."""
	if not is_earth_trading_sales_order_workflow_active():
		return
	if doc.is_new():
		return
	previous = doc.get_doc_before_save()
	if not previous:
		return
	prev_state = previous.get("workflow_state")
	new_state = doc.get("workflow_state")
	if prev_state == "ET SO Final Review" and new_state == "ET SO Pending Assignment":
		_send_approval_email_stub(doc)


def _send_approval_email_stub(doc):
	recipients: list[str] = []
	# Customer's primary contact, if resolvable
	if doc.get("contact_email"):
		recipients.append(doc.contact_email)
	# Fallback: lead_owner / owner of the SO
	if not recipients and doc.get("owner"):
		recipients.append(doc.owner)
	if not recipients:
		return
	subject = _("Sales Order {0} approved").format(doc.name)
	message = _(
		"<p>Sales Order <b>{0}</b> has been approved by the Trade Manager.</p>"
		"<p>Operations will assign a handler shortly.</p>"
		"<p><i>This is a placeholder notification. Final buyer/seller email "
		"templates are pending and will be wired in by Earth Trading admins.</i></p>"
	).format(doc.name)
	try:
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			reference_doctype="Sales Order",
			reference_name=doc.name,
			now=False,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.sales_order.approval_email")


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
