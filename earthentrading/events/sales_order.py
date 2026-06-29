# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import json

import frappe
from frappe import _

from earthentrading.api.recipients import build_recipient_candidates
from earthentrading.utils import (
	is_earth_trading_quotation_workflow_active,
	is_earth_trading_sales_order_workflow_active,
)

# States that mean the SO has cleared approval. before_submit lets any of
# these through (only "Pending Assignment" actually flips docstatus=1 the
# first time, but a doc could land in Person Assigned / Tasks Completed / etc.
# from later transitions).
POST_APPROVAL_STATES = {
	"Pending Assignment",
	"Person Assigned",
	"Tasks Completed",
	"Completed",
	"Claim",
}


def validate(doc, method):
	_sync_assigned_trader_from_items(doc)
	_reconcile_email_recipients(doc)
	_send_email_on_trader_approval(doc)


# --- Trade-email drafts (edited in the Preview dialog) ----------------------

DRAFT_FIELD = {"buyer": "custom_et_buyer_email_draft", "seller": "custom_et_seller_email_draft"}


def load_email_draft(doc, side: str) -> dict | None:
	"""Parse the saved per-side email draft (JSON: {to, cc, subject, body}).
	Returns None when nothing was saved from the Preview dialog."""
	raw = doc.get(DRAFT_FIELD.get(side))
	if not raw:
		return None
	try:
		data = json.loads(raw)
	except Exception:
		return None
	return data if isinstance(data, dict) else None


def split_emails(value) -> list[str]:
	"""Comma/semicolon/newline-separated address string -> de-duped list."""
	out: list[str] = []
	seen: set[str] = set()
	for chunk in (value or "").replace(";", ",").replace("\n", ",").split(","):
		addr = chunk.strip()
		if addr and addr.lower() not in seen:
			seen.add(addr.lower())
			out.append(addr)
	return out


def _send_email_on_trader_approval(doc):
	"""Auto-send the buyer + seller trade emails when the trade manager approves
	the deal (SO enters Final Review from Trader Manager Review, or Draft ->
	Final Review when no trader was assigned). Each side uses the trade manager's
	saved Preview draft when present, otherwise the freshly-rendered default."""
	if not is_earth_trading_sales_order_workflow_active():
		return
	if doc.is_new():
		return
	previous = doc.get_doc_before_save()
	if not previous:
		return
	prev_state = previous.get("workflow_state")
	new_state = doc.get("workflow_state")
	if new_state == "Final Review" and prev_state in ("Trader Manager Review", "Draft"):
		_send_side_email(doc, side="buyer", party_side="Customer")
		_send_side_email(doc, side="seller", party_side="Supplier")


def _send_side_email(doc, side: str, party_side: str):
	draft = load_email_draft(doc, side)
	if draft:
		to = split_emails(draft.get("to"))
		cc = split_emails(draft.get("cc"))
		subject = draft.get("subject") or _email_subject(doc)
		body = draft.get("body") or _render_confirmation_email(doc, side)
	else:
		to, cc = _collect_to_cc(doc, party_side)
		subject = _email_subject(doc)
		body = _render_confirmation_email(doc, side)
	if not to and not cc:
		return
	to_lower = {t.lower() for t in to}
	cc = [e for e in cc if e.lower() not in to_lower]
	try:
		frappe.sendmail(
			# If no To, fall back to sending to the CC list.
			recipients=to or cc,
			cc=cc if to else None,
			subject=subject,
			message=body,
			reference_doctype="Sales Order",
			reference_name=doc.name,
			now=False,
		)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(), "earthentrading.sales_order.approval_email"
		)


def _reconcile_email_recipients(doc):
	"""Keep custom_et_email_recipients in sync with the selected Customer
	(buyer) and Supplier (seller).

	- Add any missing rows from each party's primary / secondary email and
	  dealing users (defaults: primary -> To, secondary + users -> CC).
	- Preserve the Primary / CC ticks (and any manually added rows) the user
	  has already edited, matching on (party_side, email).
	- Drop a side's rows when its party link changes, so stale recipients from
	  a previously-selected Customer/Supplier don't linger.
	"""
	candidates = build_recipient_candidates(doc.get("customer"), doc.get("custom_et_supplier"))

	# Only drop a side's rows when a previously-saved party link actually
	# changed. On a brand-new doc (no prior state) we keep whatever rows are
	# already present — e.g. the client-filled rows the user may have edited
	# before the first save — and only top up missing candidates.
	prev = doc.get_doc_before_save()
	customer_changed = bool(prev) and prev.get("customer") != doc.get("customer")
	supplier_changed = bool(prev) and prev.get("custom_et_supplier") != doc.get("custom_et_supplier")

	kept_rows = []
	preserved_keys: set[tuple] = set()
	for row in doc.get("custom_et_email_recipients") or []:
		side = row.get("party_side")
		if (side == "Customer" and customer_changed) or (side == "Supplier" and supplier_changed):
			continue
		kept_rows.append(
			{
				"party_side": side,
				"source": row.get("source"),
				"recipient_name": row.get("recipient_name"),
				"email": row.get("email"),
				"is_primary": row.get("is_primary"),
				"is_cc": row.get("is_cc"),
			}
		)
		preserved_keys.add((side, (row.get("email") or "").strip().lower()))

	# Rebuild: kept rows first (order + ticks preserved), then missing candidates.
	doc.set("custom_et_email_recipients", [])
	for row in kept_rows:
		doc.append("custom_et_email_recipients", row)
	for cand in candidates:
		key = (cand["party_side"], (cand["email"] or "").strip().lower())
		if key in preserved_keys:
			continue
		doc.append("custom_et_email_recipients", cand)
		preserved_keys.add(key)


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


def _email_subject(doc) -> str:
	"""Subject shared by the buyer & seller emails:
	<SO ID> - <Buyer> - <Seller> - <Commodity> - <Shipping period> - <Port of delivery>.

	Commodity and shipping period come from the first item; port of delivery is
	the port of destination. Empty parts are dropped so the line stays clean."""
	items = doc.get("items") or []
	first = items[0] if items else None
	commodity = ""
	shipping = ""
	if first is not None:
		commodity = first.get("item_name") or first.get("item_code") or ""
		shipping = _format_shipping_period(first)
	parts = [
		doc.get("name") or _("Draft"),
		_resolve_customer_label(doc, "buyer"),
		_resolve_customer_label(doc, "seller"),
		commodity,
		shipping,
		doc.get("custom_et_port_of_destination") or "",
	]
	return " - ".join(str(p) for p in parts if p)


def _collect_to_cc(doc, side: str | None = None) -> tuple[list[str], list[str]]:
	"""Build (To, CC) from custom_et_email_recipients: rows ticked Primary go
	to To, rows ticked CC go to CC. A row with neither tick is skipped, and an
	address that is both Primary and CC stays only in To. De-duped, order
	preserved. When `side` ("Customer"/"Supplier") is given, only that side's
	rows are considered."""
	to: list[str] = []
	cc: list[str] = []
	to_seen: set[str] = set()
	cc_seen: set[str] = set()
	for row in doc.get("custom_et_email_recipients") or []:
		if side and row.get("party_side") != side:
			continue
		email = (row.get("email") or "").strip()
		if not email:
			continue
		key = email.lower()
		if row.get("is_primary"):
			if key not in to_seen:
				to_seen.add(key)
				to.append(email)
		elif row.get("is_cc"):
			if key not in cc_seen:
				cc_seen.add(key)
				cc.append(email)
	cc = [e for e in cc if e.lower() not in to_seen]
	return to, cc


def _resolve_customer_label(doc, kind: str) -> str:
	"""Human-readable name for the buyer (= Customer) or seller (= Supplier)
	side of the SO."""
	if kind == "seller":
		supplier = doc.get("custom_et_supplier")
		if supplier:
			return frappe.db.get_value("Supplier", supplier, "supplier_name") or supplier
		return "XYZ"
	# buyer = the standard customer
	return doc.get("customer_name") or doc.get("customer") or "ABC"


def _render_confirmation_email(doc, side: str = "seller") -> str:
	"""Render the trade-confirmation email. `side` is "seller" or "buyer";
	the Commission line is included only on the Seller's copy."""
	seller = _resolve_customer_label(doc, "seller")
	buyer = _resolve_customer_label(doc, "buyer")
	broker = doc.get("company") or "Earthen Trading"

	item_blocks = []
	for idx, row in enumerate(doc.get("items") or [], start=1):
		item_blocks.append(
			f"""<p><b>ITEM NO. {idx}:</b><br>
Commodity: {_e(row.get("item_name") or row.get("item_code") or "")}<br>
Price: {_format_price(row, doc)}<br>
Quantity: {_format_quantity(row)}<br>
Packaging: {_e(row.get("custom_et_packaging") or "")}<br>
Shipping Period: {_format_shipping_period(row)}
</p>"""
		)

	commission_line = ""
	if side == "seller":
		commission = _format_commission(doc)
		if commission:
			commission_line = f"<br>Commission: {_e(commission)}"

	shared = f"""<p>
Packaging Design: {_e(doc.get("custom_et_packaging_design") or "")}<br>
Origin: {_e(doc.get("custom_et_origin") or "")}<br>
Crop: {_e(doc.get("custom_et_crop") or "")}<br>
Total Quantity: {_format_total_quantity(doc)}<br>
Parity: {_e(_format_parity(doc))}<br>
Port of Loading: {_e(_format_loading_port(doc))}<br>
Payment: {_e(doc.get("custom_et_trade_payment") or "")}{commission_line}
</p>"""

	return f"""<p>Good Day!</p>
<p>Following our written exchange, we confirm that the following business has been
concluded today.</p>
<p>
<b>Seller:</b> {_e(seller)}<br>
<b>Buyer:</b> {_e(buyer)}<br>
<b>Broker:</b> {_e(broker)}
</p>
{''.join(item_blocks)}
{shared}
{_buyer_info_block(doc)}
<p>Broker Ref: {_e(doc.name or "")}</p>
<p>For clarity, please confirm your agreement by replying to this along with the signed contract.</p>
<p>Thank you for the business.</p>
"""


# ----------------- small formatting helpers -----------------------------

def _format_price(row, doc) -> str:
	rate = row.get("rate") or row.get("custom_et_traded_price")
	if rate is None:
		return ""
	currency = doc.get("currency") or "USD"
	uom = row.get("uom") or "Metric Ton"
	return f"{currency} ${rate:,.2f} per {uom}"


def _format_quantity(row) -> str:
	qty = row.get("qty")
	uom = row.get("uom") or "Metric Ton"
	if qty is None:
		return ""
	out = f"{qty:g} {uom} (+/- 5%)"
	container = (row.get("custom_et_container") or "").strip()
	if container:
		out += f" ({container})"
	return out


def _format_total_quantity(doc) -> str:
	total = doc.get("total_qty")
	if total is None:
		return ""
	out = f"{total:g} Metric Ton (+/- 5%)"
	# Append the container when the order is a single line (matches the example).
	items = doc.get("items") or []
	if len(items) == 1:
		container = (items[0].get("custom_et_container") or "").strip()
		if container:
			out += f" ({container})"
	return out


def _format_shipping_period(row) -> str:
	start = row.get("custom_et_shipping_start")
	end = row.get("custom_et_shipping_end")
	if start and end:
		return f"{frappe.utils.formatdate(start, 'dd-MM-yyyy')} to {frappe.utils.formatdate(end, 'dd-MM-yyyy')}"
	if start:
		return frappe.utils.formatdate(start, "dd-MM-yyyy")
	return ""


def _format_parity(doc) -> str:
	"""Renders as e.g. 'CIF Kolkata, India' — incoterm + port_of_destination + destination."""
	incoterm = doc.get("incoterm") or ""
	port = doc.get("custom_et_port_of_destination") or ""
	dest = doc.get("custom_et_destination") or ""
	parts: list[str] = []
	head = " ".join(p for p in (incoterm, port) if p)
	if head:
		parts.append(head)
	if dest:
		parts.append(dest)
	return ", ".join(parts)


def _format_loading_port(doc) -> str:
	port = doc.get("custom_et_port_of_loading") or ""
	origin = doc.get("custom_et_origin") or ""
	parts = [p for p in (port, origin) if p]
	return ", ".join(parts)


def _format_commission(doc) -> str:
	# Contract-level brokerage = Brokerage + Co-Brokerage (per Metric Ton).
	value = (doc.get("custom_et_brokerage_commission_value") or 0) + (
		doc.get("custom_et_co_brokerage_commission_value") or 0
	)
	currency = doc.get("currency") or "USD"
	if not value:
		return ""
	return f"{currency} ${value:g} per Metric Ton of the contract volume"


def _buyer_info_block(doc) -> str:
	"""Buyer (= the standard Customer) details appended at the end of the
	confirmation email: company name, full billing address, primary contact."""
	customer = doc.get("customer")
	if not customer:
		return ""
	name = doc.get("customer_name") or customer

	address_html = ""
	addr = doc.get("customer_address")
	if not addr:
		addr = frappe.db.get_value("Customer", customer, "customer_primary_address")
	if not addr:
		try:
			from frappe.contacts.doctype.address.address import get_default_address

			addr = get_default_address("Customer", customer)
		except Exception:
			addr = None
	if addr:
		try:
			from frappe.contacts.doctype.address.address import get_address_display

			address_html = get_address_display(addr) or ""
		except Exception:
			address_html = ""

	if not address_html and doc.get("address_display"):
		address_html = doc.get("address_display")

	contact_lines: list[str] = []
	contact_name = doc.get("contact_person")
	if not contact_name:
		contact_name = frappe.db.get_value("Customer", customer, "customer_primary_contact")
	if contact_name:
		c = (
			frappe.db.get_value(
				"Contact",
				contact_name,
				["first_name", "last_name", "email_id", "phone", "mobile_no"],
				as_dict=True,
			)
			or {}
		)
		full = " ".join(p for p in (c.get("first_name"), c.get("last_name")) if p)
		if full:
			contact_lines.append(f"Contact: {_e(full)}")
		if c.get("email_id"):
			contact_lines.append(f"Email: {_e(c.get('email_id'))}")
		phone = c.get("mobile_no") or c.get("phone")
		if phone:
			contact_lines.append(f"Phone: {_e(phone)}")

	parts = [f"<b>{_e(name)}</b>"]
	if address_html:
		parts.append(address_html)  # already-formatted HTML from get_address_display
	if contact_lines:
		parts.append("<br>".join(contact_lines))
	return "<p><b>Buyer Details:</b><br>" + "<br>".join(parts) + "</p>"


def _e(s) -> str:
	"""Minimal HTML-escape so user-typed values can't break the template."""
	if s is None:
		return ""
	return (
		str(s)
		.replace("&", "&amp;")
		.replace("<", "&lt;")
		.replace(">", "&gt;")
	)


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
		if ws != "Quote Approved":
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
