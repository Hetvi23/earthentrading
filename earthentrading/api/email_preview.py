# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Render the buyer + seller trade-confirmation emails for the Preview dialog.

Accepts either a saved Sales Order name or the in-memory form doc (JSON) so the
user can preview before saving. Returns each side's To / CC / subject / HTML.
The buyer copy omits the Commission line; the seller copy includes it.
"""

import json

import frappe
from frappe import _

from earthentrading.events.sales_order import (
	_collect_to_cc,
	_render_confirmation_email,
	_resolve_customer_label,
)


@frappe.whitelist()
def preview(sales_order: str | None = None, doc: str | None = None) -> dict:
	if doc:
		so = frappe.get_doc(json.loads(doc))
	elif sales_order:
		so = frappe.get_doc("Sales Order", sales_order)
	else:
		frappe.throw(_("Provide a Sales Order to preview."))

	out = {}
	for side, party_side in (("buyer", "Customer"), ("seller", "Supplier")):
		to, cc = _collect_to_cc(so, party_side)
		out[side] = {
			"party": _resolve_customer_label(so, side),
			"to": to,
			"cc": cc,
			"subject": _("Trade Confirmation — {0} ({1})").format(
				so.name or _("unsaved"), _resolve_customer_label(so, side)
			),
			"html": _render_confirmation_email(so, side),
		}
	return out
