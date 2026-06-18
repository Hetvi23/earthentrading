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
	"Pending Assignment",
	"In Progress",
	"Raise Invoice",
	"Completed",
	"Claim",
}


def validate(doc, method):
	_sync_assigned_trader_from_items(doc)
	_send_email_on_trader_approval(doc)


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


def _send_email_on_trader_approval(doc):
	"""Send the trade confirmation email to buyer + seller when the trade
	manager approves the deal — i.e. the SO enters Final Review. This happens
	on Trader Review -> Final Review (trade manager approving an
	assigned-trader deal) and, when no trader was assigned, on the
	Draft -> Final Review send-for-approval path. It fires BEFORE the
	operations manager's final approval. Picks the single- or multi-commodity
	template based on the number of items on the SO."""
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
		_send_approval_email(doc)


def _send_approval_email(doc):
	recipients = _collect_recipients(doc)
	if not recipients:
		return
	body = _render_confirmation_email(doc)
	subject = _("Trade Confirmation — {0} ({1})").format(
		doc.name, _resolve_customer_label(doc, "buyer")
	)
	try:
		frappe.sendmail(
			recipients=recipients,
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


def _collect_recipients(doc) -> list[str]:
	"""Buyer (custom_et_buyer) + Seller (customer) primary contact emails
	+ contact_email on the SO itself. De-duped, empty values stripped."""
	emails: list[str] = []
	for customer_field in ("custom_et_buyer", "customer"):
		cust = doc.get(customer_field)
		if not cust:
			continue
		em = _primary_email_for_customer(cust)
		if em:
			emails.append(em)
	if doc.get("contact_email"):
		emails.append(doc.contact_email)
	# De-dupe preserving order
	seen: set[str] = set()
	out: list[str] = []
	for e in emails:
		e = (e or "").strip()
		if not e or e in seen:
			continue
		seen.add(e)
		out.append(e)
	return out


def _primary_email_for_customer(customer: str) -> str | None:
	"""Best-effort lookup of a customer's primary contact email via
	Dynamic Link → Contact → email_ids."""
	contact = frappe.db.sql(
		"""
		SELECT c.name
		FROM `tabContact` c
		JOIN `tabDynamic Link` dl ON dl.parent = c.name AND dl.parenttype = 'Contact'
		WHERE dl.link_doctype = 'Customer'
		  AND dl.link_name = %s
		ORDER BY c.is_primary_contact DESC, c.modified DESC
		LIMIT 1
		""",
		customer,
		as_dict=True,
	)
	if not contact:
		return None
	row = frappe.db.get_value(
		"Contact Email",
		{"parent": contact[0].name, "is_primary": 1},
		"email_id",
	) or frappe.db.get_value(
		"Contact Email", {"parent": contact[0].name}, "email_id"
	)
	return row


def _resolve_customer_label(doc, kind: str) -> str:
	"""Return the human-readable Customer Name for the seller or buyer
	side of the SO."""
	if kind == "buyer":
		return (
			(doc.get("custom_et_buyer") and frappe.db.get_value(
				"Customer", doc.custom_et_buyer, "customer_name"
			))
			or doc.customer_name
			or doc.customer
			or "ABC"
		)
	return doc.customer_name or doc.customer or "XYZ"


def _render_confirmation_email(doc) -> str:
	"""Pick the right template based on # of items and substitute fields."""
	items = doc.get("items") or []
	if len(items) <= 1:
		return _render_single_commodity_email(doc)
	return _render_multi_commodity_email(doc)


def _render_single_commodity_email(doc) -> str:
	seller = _resolve_customer_label(doc, "seller")
	buyer = _resolve_customer_label(doc, "buyer")
	broker = doc.get("company") or "Earthen Trading"
	row = (doc.get("items") or [{}])[0]

	parity = _format_parity(doc)
	port_of_loading = _format_loading_port(doc)
	commission = _format_commission(doc)

	specs = (row.get("description") or "").strip()
	specs_html = ""
	if specs:
		specs_html = (
			"<p><b>Specification:</b><br>"
			+ specs.replace("\n", "<br>")
			+ "</p>"
		)

	return f"""<p>Good Day!</p>
<p>As per our discussion over whatsapp here I confirm the business as per the
following. Kindly send us the contract at your earliest.</p>
<p>
<b>Seller:</b> {_e(seller)}<br>
<b>Buyer:</b> {_e(buyer)}<br>
<b>Broker:</b> {_e(broker)}
</p>
<p><b>ITEM NO. 1:</b><br>
Commodity: {_e(row.get("item_name") or row.get("item_code") or "")}<br>
Price: {_format_price(row, doc)}<br>
Quantity: {_format_quantity(row)}<br>
Packaging: {_e(row.get("custom_et_packaging") or "")}<br>
Shipping Period: {_format_shipping_period(row)}<br>
Packaging Design: {_e(doc.get("custom_et_packaging_design") or "")}<br>
Origin: {_e(doc.get("custom_et_origin") or "")}<br>
Crop: {_e(doc.get("custom_et_crop") or "")}<br>
Total Quantity: {_format_total_quantity(doc)}<br>
Parity: {_e(parity)}<br>
Port of Loading: {_e(port_of_loading)}<br>
Payment: {_e(doc.get("custom_et_trade_payment") or "")}<br>
Commission: {_e(commission)}
</p>
{specs_html}
"""


def _render_multi_commodity_email(doc) -> str:
	seller = _resolve_customer_label(doc, "seller")
	buyer = _resolve_customer_label(doc, "buyer")
	broker = doc.get("company") or "Earthen Trading"

	items_html_parts = []
	for idx, row in enumerate(doc.get("items") or [], start=1):
		commission = _format_commission(doc)
		specs = (row.get("description") or "").strip()
		specs_html = ""
		if specs:
			specs_html = (
				"<p><b>Specifications:</b><br>"
				+ specs.replace("\n", "<br>")
				+ "</p>"
			)
		items_html_parts.append(
			f"""<p><b>ITEM NO. {idx}:</b><br>
Commodity: {_e(row.get("item_name") or row.get("item_code") or "")}<br>
Price: {_format_price(row, doc)}<br>
Quantity: {_format_quantity(row)}<br>
Packaging: {_e(row.get("custom_et_packaging") or "")}<br>
Shipping Period: {_format_shipping_period(row)}<br>
Broker's Commission: {_e(commission)}
</p>
{specs_html}"""
		)

	parity = _format_parity(doc)
	port_of_loading = _format_loading_port(doc)

	return f"""<p>Good Day,</p>
<p>Following our written exchange, we confirm that the following business has been
concluded today.</p>
<p>
<b>Seller:</b> {_e(seller)}<br>
<b>Buyer:</b> {_e(buyer)}<br>
<b>Broker:</b> {_e(broker)}
</p>
{''.join(items_html_parts)}
<p>
Origin: {_e(doc.get("custom_et_origin") or "")}<br>
Crop: {_e(doc.get("custom_et_crop") or "")}<br>
Parity: {_e(parity)}<br>
Port of Loading: {_e(port_of_loading)}<br>
Payment: {_e(doc.get("custom_et_trade_payment") or "")}
</p>
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
	return f"{qty:g} {uom}"


def _format_total_quantity(doc) -> str:
	total = doc.get("total_qty")
	if total is None:
		return ""
	return f"{total:g} Metric Ton"


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
	value = doc.get("custom_et_brokerage_commission_value") or 0
	unit = doc.get("custom_et_brokerage_commission_unit") or "Metric Ton"
	currency = doc.get("currency") or "USD"
	if not value:
		return ""
	return f"{currency} ${value:g} per {unit} of the contract volume"


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
