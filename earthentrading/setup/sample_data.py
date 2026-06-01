# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Sample data seed — Items, Customers, Suppliers, Leads with Trade Report
rows, submitted Sales Orders across multiple years, and Projects with ET
Task Templates assigned.

Idempotent: re-running skips rows that already exist by primary key.
Designed to be safe on top of a fresh ERPNext + earthentrading site.

Run with:
    bench --site <site> execute earthentrading.setup.sample_data.run
"""

from __future__ import annotations

import random

import frappe
from frappe.utils import getdate

from earthentrading.events.project import spawn_et_checklist_from_project


ITEM_GROUPS = ["Pulses", "Spices", "Nuts", "Grains", "Sugar", "Feed", "Rice"]

# (item_code, item_name, item_group)
ITEMS = [
	("PULSE-YELLOW-PEAS", "Yellow Peas", "Pulses"),
	("PULSE-PIGEON-PEAS", "Pigeon Peas", "Pulses"),
	("PULSE-BLACK-MATPE", "Black Matpe", "Pulses"),
	("PULSE-RED-LENTILS", "Nipper Red Lentils", "Pulses"),
	("SPICE-STONE-FLOWER", "Stone Flower", "Spices"),
	("SPICE-CUMIN", "Cumin", "Spices"),
	("NUT-CASHEW-W320", "Cashew W320", "Nuts"),
	("NUT-ALMOND", "California Almond", "Nuts"),
	("GRAIN-WHEAT", "Wheat", "Grains"),
	("GRAIN-MAIZE", "Yellow Maize", "Grains"),
	("RICE-BASMATI", "Basmati Rice", "Rice"),
	("RICE-PARBOILED", "Parboiled Rice", "Rice"),
	("SUGAR-ICUMSA-45", "Sugar ICUMSA-45", "Sugar"),
	("FEED-SOYABEAN-MEAL", "Soyabean Meal", "Feed"),
]

# Customers — mix of brokers (buyer side) and end-buyers
CUSTOMERS = [
	("Aavatto Brokerage Pvt Ltd", "Commercial"),
	("Sahara Grains Trading Co", "Commercial"),
	("Mumbai Pulse Traders", "Commercial"),
	("Pacific Rim Imports", "Commercial"),
	("Delhi Spice House", "Commercial"),
	("Crescent Foods LLC", "Commercial"),
	("Lagos Trading Group", "Commercial"),
	("Singapore Commodities Pte", "Commercial"),
	("Bangalore Wholesale Markets", "Commercial"),
	("Dubai Agro Holdings", "Commercial"),
]

# Suppliers — external brokers
SUPPLIERS = [
	("Andean Pulses Cooperative", "All Supplier Groups"),
	("Myanmar Bean Exporters", "All Supplier Groups"),
	("Sudan Agri Brokers", "All Supplier Groups"),
	("Australian Pulse Growers", "All Supplier Groups"),
	("Canadian Grain Brokers", "All Supplier Groups"),
]

# Leads — (organization_name, lead_function, commodity_group, country,
#         internal_broker (email), external_broker (supplier name),
#         trade_report rows = list of (transaction, commodity, origin, destination, role))
LEADS = [
	(
		"Sahara Grains Trading Co",
		"Buyer",
		"Pulses",
		"Nigeria",
		None,
		"Andean Pulses Cooperative",
		[
			("TR-001", "Yellow Peas", "Canada", "Nigeria", "Buyer"),
			("TR-002", "Pigeon Peas", "Sudan", "India", "Buyer"),
			("TR-003", "Black Matpe", "Myanmar", "India", "Buyer"),
		],
	),
	(
		"Pacific Rim Imports",
		"Buyer",
		"Grains",
		"Australia",
		None,
		"Australian Pulse Growers",
		[
			("TR-004", "Wheat", "Australia", "India", "Buyer"),
			("TR-005", "Yellow Maize", "Brazil", "Vietnam", "Buyer"),
		],
	),
	(
		"Delhi Spice House",
		"Buyer-Seller",
		"Spices",
		"India",
		None,
		None,
		[
			("TR-006", "Cumin", "India", "Singapore", "Seller"),
			("TR-007", "Stone Flower", "India", "Dubai", "Seller"),
		],
	),
	(
		"Crescent Foods LLC",
		"Buyer",
		"Rice",
		"United States",
		None,
		"Canadian Grain Brokers",
		[
			("TR-008", "Basmati Rice", "India", "United States", "Buyer"),
			("TR-009", "Parboiled Rice", "Thailand", "United States", "Buyer"),
		],
	),
	(
		"Mumbai Pulse Traders",
		"Buyer-Seller",
		"Pulses",
		"India",
		None,
		"Myanmar Bean Exporters",
		[
			("TR-010", "Black Matpe", "Myanmar", "India", "Buyer"),
			("TR-011", "Nipper Red Lentils", "Australia", "India", "Buyer"),
			("TR-012", "Yellow Peas", "Canada", "Bangladesh", "Seller"),
		],
	),
	(
		"Lagos Trading Group",
		"Seller",
		"Pulses",
		"Nigeria",
		None,
		"Sudan Agri Brokers",
		[
			("TR-013", "Pigeon Peas", "Nigeria", "India", "Seller"),
			("TR-014", "Cowpeas", "Nigeria", "Sudan", "Seller"),
		],
	),
	(
		"Singapore Commodities Pte",
		"Broker",
		"Pulses",
		"Singapore",
		None,
		None,
		[
			("TR-015", "Yellow Peas", "Russia", "Vietnam", "Broker"),
			("TR-016", "Pigeon Peas", "Tanzania", "India", "Broker"),
		],
	),
	(
		"Bangalore Wholesale Markets",
		"Buyer",
		"Spices",
		"India",
		None,
		None,
		[("TR-017", "Cumin", "India", "Sri Lanka", "Seller")],
	),
	(
		"Dubai Agro Holdings",
		"Buyer",
		"Nuts",
		"United Arab Emirates",
		None,
		None,
		[
			("TR-018", "Cashew W320", "Vietnam", "United Arab Emirates", "Buyer"),
			("TR-019", "California Almond", "United States", "United Arab Emirates", "Buyer"),
		],
	),
	(
		"Aavatto Brokerage Pvt Ltd",
		"Broker",
		"Pulses",
		"India",
		None,
		None,
		[
			("TR-020", "Yellow Peas", "Canada", "Nigeria", "Broker"),
			("TR-021", "Pigeon Peas", "Sudan", "India", "Broker"),
			("TR-022", "Black Matpe", "Myanmar", "India", "Broker"),
		],
	),
]

# Sales Orders — (transaction_date, customer, buyer (end-buyer customer), item_code, qty_mt, rate_usd, origin, destination)
SALES_ORDERS = [
	("2024-03-15", "Aavatto Brokerage Pvt Ltd", "Sahara Grains Trading Co", "PULSE-YELLOW-PEAS", 500, 420, "Canada", "Nigeria"),
	("2024-04-10", "Aavatto Brokerage Pvt Ltd", "Mumbai Pulse Traders", "PULSE-PIGEON-PEAS", 750, 850, "Sudan", "India"),
	("2024-06-20", "Pacific Rim Imports", "Pacific Rim Imports", "GRAIN-WHEAT", 1200, 280, "Australia", "India"),
	("2024-08-05", "Delhi Spice House", "Bangalore Wholesale Markets", "SPICE-CUMIN", 80, 2500, "India", "Singapore"),
	("2024-09-12", "Crescent Foods LLC", "Crescent Foods LLC", "RICE-BASMATI", 250, 1400, "India", "United States"),
	("2024-11-18", "Mumbai Pulse Traders", "Mumbai Pulse Traders", "PULSE-BLACK-MATPE", 400, 1100, "Myanmar", "India"),
	("2025-02-08", "Aavatto Brokerage Pvt Ltd", "Lagos Trading Group", "PULSE-PIGEON-PEAS", 600, 920, "Nigeria", "India"),
	("2025-03-22", "Singapore Commodities Pte", "Singapore Commodities Pte", "PULSE-YELLOW-PEAS", 1000, 440, "Russia", "Vietnam"),
	("2025-05-14", "Dubai Agro Holdings", "Dubai Agro Holdings", "NUT-CASHEW-W320", 60, 6800, "Vietnam", "United Arab Emirates"),
	("2025-07-30", "Aavatto Brokerage Pvt Ltd", "Sahara Grains Trading Co", "PULSE-RED-LENTILS", 350, 1250, "Australia", "Nigeria"),
	("2025-10-11", "Delhi Spice House", "Bangalore Wholesale Markets", "SPICE-STONE-FLOWER", 28, 1400, "Nigeria", "India"),
	("2025-12-03", "Mumbai Pulse Traders", "Mumbai Pulse Traders", "PULSE-BLACK-MATPE", 550, 1180, "Myanmar", "India"),
	("2026-01-19", "Pacific Rim Imports", "Pacific Rim Imports", "GRAIN-MAIZE", 1500, 240, "Brazil", "Vietnam"),
	("2026-03-07", "Aavatto Brokerage Pvt Ltd", "Crescent Foods LLC", "RICE-PARBOILED", 300, 1320, "Thailand", "United States"),
	("2026-04-25", "Dubai Agro Holdings", "Dubai Agro Holdings", "NUT-ALMOND", 45, 9200, "United States", "United Arab Emirates"),
]

CONTRACT_TYPES = ["Brokerage", "Direct (Back to Back)", "To Seller", "To Buyer"]
PACKAGING_DESIGNS = ["Seller's Design", "Buyer's Design"]
PORTS_BY_COUNTRY = {
	"Canada": ("Vancouver", "Halifax"),
	"Nigeria": ("Lagos", "Apapa"),
	"Sudan": ("Port Sudan", "Khartoum"),
	"India": ("Nhava Sheva", "Mundra"),
	"Myanmar": ("Yangon", "Yangon"),
	"Australia": ("Melbourne", "Sydney"),
	"Brazil": ("Santos", "Paranagua"),
	"Vietnam": ("Ho Chi Minh", "Haiphong"),
	"Singapore": ("Singapore", "Singapore"),
	"Bangladesh": ("Chittagong", "Dhaka"),
	"Russia": ("Novorossiysk", "St Petersburg"),
	"Tanzania": ("Dar es Salaam", "Tanga"),
	"United States": ("Los Angeles", "New York"),
	"Sri Lanka": ("Colombo", "Hambantota"),
	"United Arab Emirates": ("Jebel Ali", "Sharjah"),
	"Thailand": ("Bangkok", "Laem Chabang"),
}

# Projects — (project_name, template_code)
PROJECTS = [
	("ET Demo - Yellow Peas to Nigeria", "brokerage"),
	("ET Demo - Pigeon Peas direct B2B", "trading_direct_b2b"),
	("ET Demo - Wheat to Buyer Australia→India", "trading_to_buyer"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _company():
	return frappe.db.get_single_value("Global Defaults", "default_company")


def _ensure_item_groups():
	for ig in ITEM_GROUPS:
		if frappe.db.exists("Item Group", ig):
			continue
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": ig,
				"parent_item_group": frappe.db.get_value(
					"Item Group", {"is_group": 1}, "name", order_by="lft asc"
				) or "All Item Groups",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)


def _ensure_uom_mt():
	if not frappe.db.exists("UOM", "Metric Ton"):
		frappe.get_doc(
			{"doctype": "UOM", "uom_name": "Metric Ton", "must_be_whole_number": 0}
		).insert(ignore_permissions=True)


def _ensure_items():
	for code, name, group in ITEMS:
		if frappe.db.exists("Item", code):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": name,
				"item_group": group,
				"stock_uom": "Metric Ton",
				"is_stock_item": 0,
				"is_sales_item": 1,
				"is_purchase_item": 1,
				"include_item_in_manufacturing": 0,
			}
		).insert(ignore_permissions=True)


def _ensure_customers():
	for name, cgroup in CUSTOMERS:
		if frappe.db.exists("Customer", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": "Company",
				"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups",
				"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name") or "All Territories",
			}
		).insert(ignore_permissions=True)


def _ensure_suppliers():
	for name, sgroup in SUPPLIERS:
		if frappe.db.exists("Supplier", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Supplier",
				"supplier_name": name,
				"supplier_type": "Company",
				"supplier_group": frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or "All Supplier Groups",
				"country": frappe.db.get_single_value("Global Defaults", "country") or "India",
			}
		).insert(ignore_permissions=True)


def _country_or_none(name: str | None) -> str | None:
	if not name:
		return None
	return name if frappe.db.exists("Country", name) else None


def _ensure_leads():
	for org, fn, cg, country, internal, external, trade_rows in LEADS:
		# de-dupe by company_name
		existing = frappe.db.exists("Lead", {"company_name": org})
		if existing:
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Lead",
				"lead_name": org,
				"company_name": org,
				"status": "Open",
				"country": _country_or_none(country),
				"custom_et_lead_function": fn if frappe.db.exists("ET Lead Function", fn) else None,
				"custom_et_commodity_group": cg if frappe.db.exists("Item Group", cg) else None,
				"custom_et_external_broker": external if external and frappe.db.exists("Supplier", external) else None,
				"custom_et_sales_stage": "Lead",
			}
		)
		for tr in trade_rows:
			tx, commodity, origin, dest, role = tr
			doc.append(
				"custom_et_trade_report",
				{
					"transaction_id": tx,
					"commodity": commodity,
					"origin": _country_or_none(origin),
					"destination": _country_or_none(dest),
					"role": role,
				},
			)
		doc.insert(ignore_permissions=True)


def _disabled_workflows():
	"""Yield (workflow_name, prev_is_active) for SO/Quotation workflows we
	temporarily disable during seeding. Restored by the caller."""
	out = []
	for wf in frappe.get_all(
		"Workflow",
		filters={"document_type": ["in", ["Sales Order", "Quotation"]], "is_active": 1},
		pluck="name",
	):
		out.append(wf)
		frappe.db.set_value("Workflow", wf, "is_active", 0)
	frappe.db.commit()
	frappe.clear_cache()
	return out


def _restore_workflows(names):
	for wf in names:
		frappe.db.set_value("Workflow", wf, "is_active", 1)
	frappe.db.commit()
	frappe.clear_cache()


def _ensure_sales_orders():
	company = _company()
	uom = "Metric Ton"
	# Wipe any half-inserted drafts from a previous failed run so the loop is
	# clean and dashboard-visible (charts filter to docstatus=1).
	stale_drafts = frappe.get_all(
		"Sales Order",
		filters={"title": ["like", "ET-DEMO-%"], "docstatus": 0},
		pluck="name",
	)
	for n in stale_drafts:
		frappe.delete_doc("Sales Order", n, force=True, ignore_permissions=True)

	for idx, (txn_date, cust, buyer, item_code, qty, rate, origin, dest) in enumerate(SALES_ORDERS):
		title = f"ET-DEMO-{idx + 1:03d}"
		# Already submitted? skip.
		if frappe.db.exists("Sales Order", {"title": title, "docstatus": 1}):
			continue
		port_loading = PORTS_BY_COUNTRY.get(origin, ("Unknown",))[0]
		port_dest = PORTS_BY_COUNTRY.get(dest, ("Unknown",))[0]
		crop_year = str(getdate(txn_date).year - 1)
		contract = random.choice(CONTRACT_TYPES)
		packaging = random.choice(PACKAGING_DESIGNS)
		delivery_date = frappe.utils.add_months(txn_date, 2)

		doc = frappe.get_doc(
			{
				"doctype": "Sales Order",
				"title": title,
				"customer": cust,
				"transaction_date": txn_date,
				"delivery_date": delivery_date,
				"company": company,
				"order_type": "Sales",
				"po_no": f"PO-{title}",
				"po_date": txn_date,
				"currency": "USD",
				"conversion_rate": 83.0,
				"selling_price_list": frappe.db.get_value("Price List", {"selling": 1}, "name") or "Standard Selling",
				"price_list_currency": "USD",
				"plc_conversion_rate": 83.0,
				"custom_et_contract_type": contract,
				"custom_et_buyer": buyer,
				"custom_et_brokerage_commission_value": 20,
				"custom_et_co_brokerage_commission_value": 0,
				"custom_et_insurance_value": 0,
				"custom_et_brokerage_commission_unit": uom,
				"custom_et_trade_payment": "20% Advance 80% by wire transfer on presentation of documents to Buyer's Bank",
				"custom_et_port_of_loading": port_loading,
				"custom_et_origin": _country_or_none(origin),
				"custom_et_packaging_design": packaging,
				"custom_et_crop": crop_year,
				"custom_et_destination": _country_or_none(dest),
				"custom_et_port_of_destination": port_dest,
				"custom_et_deal_type": "Brokerage" if contract == "Brokerage" else "Principal",
				"items": [
					{
						"item_code": item_code,
						"qty": qty,
						"uom": uom,
						"stock_uom": uom,
						"conversion_factor": 1,
						"rate": rate,
						"delivery_date": delivery_date,
						"custom_et_packaging": "7KG PP Bags",
						"custom_et_shipping_start": txn_date,
						"custom_et_shipping_end": frappe.utils.add_days(txn_date, 26),
						"custom_et_traded_price": rate,
					}
				],
			}
		)
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		# After insert, set workflow_state to Approved directly in DB so the
		# before_submit gate in events/sales_order.py passes; the workflow
		# itself is also disabled during seeding (see _disabled_workflows).
		frappe.db.set_value(
			"Sales Order", doc.name, "workflow_state", "ET SO Approved", update_modified=False
		)
		doc.reload()
		doc.submit()


def _ensure_projects():
	company = _company()
	for pname, tpl in PROJECTS:
		if frappe.db.exists("Project", {"project_name": pname}):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Project",
				"project_name": pname,
				"company": company,
				"status": "Open",
				"custom_et_task_template": tpl if frappe.db.exists("ET Task Template", tpl) else None,
			}
		)
		doc.insert(ignore_permissions=True)
		# project after_insert hook should already spawn, but call directly so reruns
		# on existing-but-unspawned projects still create tasks.
		if doc.get("custom_et_task_template") and not doc.get("custom_et_checklist_spawned"):
			doc = frappe.get_doc("Project", doc.name)
			spawn_et_checklist_from_project(doc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run():
	random.seed(42)
	if not _company():
		frappe.throw("No default Company set — run ERPNext setup wizard first.")
	_ensure_item_groups()
	_ensure_uom_mt()
	_ensure_items()
	_ensure_customers()
	_ensure_suppliers()
	_ensure_leads()
	disabled = _disabled_workflows()
	try:
		_ensure_sales_orders()
	finally:
		_restore_workflows(disabled)
	_ensure_projects()
	frappe.db.commit()
	print("Sample data seed: done")
