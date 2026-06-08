# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Override erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice
to enforce: a Sales Invoice can only be created when the SO is in
"ET SO Raise Invoice" workflow state. Operations must mark all project
tasks done first; accounts users only see Create > Sales Invoice then."""

import frappe
from frappe import _

from erpnext.selling.doctype.sales_order.sales_order import (
	make_sales_invoice as erpnext_make_sales_invoice,
)


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None, ignore_permissions=False, args=None):
	from earthentrading.utils import is_earth_trading_sales_order_workflow_active

	if is_earth_trading_sales_order_workflow_active():
		ws = frappe.db.get_value("Sales Order", source_name, "workflow_state")
		if ws != "ET SO Raise Invoice":
			frappe.throw(
				_(
					"Sales Invoice can only be created when the Sales Order is in "
					"<b>Raise Invoice</b> state (current: <b>{0}</b>). "
					"Mark all project tasks complete first."
				).format(ws or _("unset"))
			)

	return erpnext_make_sales_invoice(
		source_name, target_doc=target_doc, ignore_permissions=ignore_permissions, args=args
	)
