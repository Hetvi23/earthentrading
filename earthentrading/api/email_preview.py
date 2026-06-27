# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Render and persist the buyer + seller trade-confirmation emails for the
Preview dialog.

`preview` accepts either a saved Sales Order name or the in-memory form doc
(JSON). For each side it returns the trade manager's saved draft (To / CC /
subject / body) when one exists, otherwise the freshly-rendered default. The
buyer copy omits the Commission line; the seller copy includes it.

`save_draft` stores whatever the trade manager edited as a per-side JSON draft
on the Sales Order. The auto-send on approval
(earthentrading.events.sales_order) then ships that exact content.
"""

import json

import frappe
from frappe import _

from earthentrading.events.sales_order import (
	DRAFT_FIELD,
	_collect_to_cc,
	_email_subject,
	_render_confirmation_email,
	_resolve_customer_label,
	load_email_draft,
	split_emails,
)


@frappe.whitelist()
def preview(sales_order: str | None = None, doc: str | None = None) -> dict:
	if doc:
		so = frappe.get_doc(json.loads(doc))
	elif sales_order:
		so = frappe.get_doc("Sales Order", sales_order)
	else:
		frappe.throw(_("Provide a Sales Order to preview."))

	default_subject = _email_subject(so)
	out = {}
	for side, party_side in (("buyer", "Customer"), ("seller", "Supplier")):
		draft = load_email_draft(so, side)
		if draft:
			to = split_emails(draft.get("to"))
			cc = split_emails(draft.get("cc"))
			subject = draft.get("subject") or default_subject
			html = draft.get("body") or _render_confirmation_email(so, side)
		else:
			to, cc = _collect_to_cc(so, party_side)
			subject = default_subject
			html = _render_confirmation_email(so, side)
		out[side] = {
			"party": _resolve_customer_label(so, side),
			"to": to,
			"cc": cc,
			"subject": subject,
			"html": html,
			"edited": bool(draft),
		}
	return out


@frappe.whitelist()
def save_draft(sales_order: str, buyer: str | None = None, seller: str | None = None) -> dict:
	"""Persist the per-side email drafts (JSON strings: {to, cc, subject, body})
	edited in the Preview dialog. Only the Trade Manager (or an admin) may save."""
	if not sales_order or not frappe.db.exists("Sales Order", sales_order):
		frappe.throw(_("Save the Sales Order before editing the email."))
	if not frappe.has_permission("Sales Order", "write", doc=sales_order):
		frappe.throw(_("You are not permitted to edit this Sales Order."), frappe.PermissionError)
	if frappe.session.user != "Administrator" and not (
		set(frappe.get_roles()) & {"ET Trader Manager", "Sales Manager", "System Manager"}
	):
		frappe.throw(
			_("Only the Trade Manager can edit the trade email."), frappe.PermissionError
		)

	# Validate the payloads are JSON objects before storing.
	def _clean(payload):
		if not payload:
			return None
		try:
			data = json.loads(payload)
		except Exception:
			frappe.throw(_("Invalid email draft."))
		return json.dumps(data) if isinstance(data, dict) else None

	frappe.db.set_value(
		"Sales Order",
		sales_order,
		{
			DRAFT_FIELD["buyer"]: _clean(buyer),
			DRAFT_FIELD["seller"]: _clean(seller),
		},
		update_modified=False,
	)
	return {"ok": True}
