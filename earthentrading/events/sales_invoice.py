# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""When every Sales Invoice for a Sales Order is fully paid, auto-transition
the SO workflow from Raise Invoice → Completed."""

import frappe


def on_submit(doc, method):
	# Submitting a SI may already mark it Paid (advance payments / cash).
	_maybe_complete_linked_sales_orders(doc)


def on_update_after_submit(doc, method):
	# outstanding_amount changes after submit when payments come in.
	_maybe_complete_linked_sales_orders(doc)


def on_payment_entry_submit(doc, method):
	"""Hook from Payment Entry on_submit — walk to each referenced Sales Order."""
	for ref in doc.get("references") or []:
		if ref.reference_doctype == "Sales Invoice" and ref.reference_name:
			si = frappe.get_doc("Sales Invoice", ref.reference_name)
			_maybe_complete_linked_sales_orders(si)
		elif ref.reference_doctype == "Sales Order" and ref.reference_name:
			_maybe_complete_sales_order(ref.reference_name)


def _maybe_complete_linked_sales_orders(si_doc):
	"""Given a Sales Invoice, find each Sales Order it touches and check if all
	invoices for that SO are fully paid."""
	if not si_doc or si_doc.docstatus != 1:
		return
	so_names: set[str] = set()
	for row in si_doc.get("items") or []:
		if row.get("sales_order"):
			so_names.add(row.sales_order)
	for so in so_names:
		_maybe_complete_sales_order(so)


def _maybe_complete_sales_order(sales_order_name: str):
	ws = frappe.db.get_value("Sales Order", sales_order_name, "workflow_state")
	if ws != "Raise Invoice":
		# Only transition from Raise Invoice. If SO is still In Progress or
		# already Completed, do nothing.
		return

	# Total outstanding across all submitted Sales Invoices for this SO.
	rows = frappe.db.sql(
		"""
		SELECT DISTINCT si.name, si.outstanding_amount, si.status
		FROM `tabSales Invoice` si
		JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
		WHERE sii.sales_order = %s AND si.docstatus = 1
		""",
		sales_order_name,
		as_dict=True,
	)
	if not rows:
		return
	total_outstanding = sum((r.outstanding_amount or 0) for r in rows)
	# Allow tiny rounding noise
	if total_outstanding > 0.01:
		return

	try:
		frappe.db.set_value(
			"Sales Order",
			sales_order_name,
			"workflow_state",
			"Completed",
			update_modified=False,
		)
		frappe.db.commit()
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"earthentrading.sales_invoice.complete_so.{sales_order_name}",
		)
