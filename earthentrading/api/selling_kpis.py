# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Selling-workspace KPIs.

- book_value(period, status): total value from Sales Orders.
    * Estimated -> all submitted SOs in the period.
    * Paid      -> SOs that have a submitted Sales Invoice whose outstanding is 0.
- trader_revenue(period): per-trader revenue. For each submitted SO with a
  commission value, gross = total_qty * (brokerage + co-brokerage) per unit,
  converted to company currency. Each trader (Assigned Trader and Co-Trader)
  earns gross * their own User 'commission %'.

All amounts are in company currency (base_*), so values across mixed-currency
SOs sum correctly.
"""

import frappe
from frappe.utils import flt, get_first_day, get_last_day, getdate, today


# ----------------------------- helpers ---------------------------------

def _period_range(period: str | None):
	"""Return (start, end) dates for a period key, or (None, None) for all-time."""
	t = getdate(today())
	if period == "this_month":
		return get_first_day(t), get_last_day(t)
	if period == "this_quarter":
		start_month = ((t.month - 1) // 3) * 3 + 1
		start = getdate(f"{t.year}-{start_month:02d}-01")
		return start, get_last_day(getdate(f"{t.year}-{start_month + 2:02d}-01"))
	if period == "this_year":
		return getdate(f"{t.year}-01-01"), getdate(f"{t.year}-12-31")
	if period == "last_year":
		return getdate(f"{t.year - 1}-01-01"), getdate(f"{t.year - 1}-12-31")
	return None, None


def _company_currency() -> str:
	company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)
	if company:
		cur = frappe.db.get_value("Company", company, "default_currency")
		if cur:
			return cur
	return frappe.db.get_default("currency") or "INR"


def _submitted_so_where(period):
	start, end = _period_range(period)
	conditions = ["docstatus = 1"]
	values: dict = {}
	if start and end:
		conditions.append("transaction_date BETWEEN %(start)s AND %(end)s")
		values["start"] = start
		values["end"] = end
	return " AND ".join(conditions), values


def _paid_sales_orders() -> set[str]:
	"""SOs that have at least one submitted Sales Invoice and whose total
	outstanding across those invoices is 0."""
	rows = frappe.db.sql(
		"""
		SELECT DISTINCT soi.sales_order AS so, si.name AS inv, si.outstanding_amount AS outstanding
		FROM `tabSales Invoice Item` soi
		JOIN `tabSales Invoice` si ON si.name = soi.parent
		WHERE si.docstatus = 1 AND soi.sales_order IS NOT NULL AND soi.sales_order != ''
		""",
		as_dict=True,
	)
	outstanding: dict[str, float] = {}
	for r in rows:
		outstanding[r.so] = outstanding.get(r.so, 0.0) + flt(r.outstanding)
	return {so for so, total in outstanding.items() if total == 0}


# ----------------------------- endpoints -------------------------------

@frappe.whitelist()
def book_value(period: str = "this_year", status: str = "Estimated") -> dict:
	where, values = _submitted_so_where(period)
	so_rows = frappe.db.sql(
		f"SELECT name, base_grand_total FROM `tabSales Order` WHERE {where}",
		values,
		as_dict=True,
	)

	if status == "Paid":
		paid = _paid_sales_orders()
		so_rows = [r for r in so_rows if r.name in paid]

	total = sum(flt(r.base_grand_total) for r in so_rows)
	return {
		"value": total,
		"currency": _company_currency(),
		"count": len(so_rows),
		"status": status,
		"period": period,
	}


@frappe.whitelist()
def trader_revenue(period: str = "this_year") -> dict:
	where, values = _submitted_so_where(period)
	sos = frappe.db.sql(
		f"""
		SELECT name, total_qty, conversion_rate,
		       custom_et_brokerage_commission_value AS brokerage,
		       custom_et_co_brokerage_commission_value AS co_brokerage,
		       custom_et_assigned_trader AS assigned_trader,
		       custom_et_co_trader AS co_trader
		FROM `tabSales Order` WHERE {where}
		""",
		values,
		as_dict=True,
	)

	pct_cache: dict[str, float] = {}

	def commission_pct(user: str | None) -> float:
		if not user:
			return 0.0
		if user not in pct_cache:
			pct_cache[user] = flt(frappe.db.get_value("User", user, "custom_et_commission_pct"))
		return pct_cache[user]

	revenue: dict[str, float] = {}
	for so in sos:
		rate = flt(so.brokerage) + flt(so.co_brokerage)  # per-unit commission
		if rate <= 0:
			continue
		# gross in company currency
		gross = flt(so.total_qty) * rate * (flt(so.conversion_rate) or 1.0)
		if gross <= 0:
			continue
		for user in (so.assigned_trader, so.co_trader):
			pct = commission_pct(user)
			if not user or pct <= 0:
				continue
			revenue[user] = revenue.get(user, 0.0) + gross * pct / 100.0

	rows = [
		{
			"trader": user,
			"full_name": frappe.db.get_value("User", user, "full_name") or user,
			"revenue": amount,
		}
		for user, amount in revenue.items()
	]
	rows.sort(key=lambda r: r["revenue"], reverse=True)
	return {"currency": _company_currency(), "rows": rows}
