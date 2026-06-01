"""Throwaway helpers used while bootstrapping the demo site."""

import frappe


def report():
	out = {
		"companies": frappe.db.count("Company"),
		"fiscal_years": frappe.db.count("Fiscal Year"),
		"customers": frappe.db.count("Customer"),
		"items": frappe.db.count("Item"),
		"suppliers": frappe.db.count("Supplier"),
		"projects": frappe.db.count("Project"),
		"sales_orders": frappe.db.count("Sales Order"),
		"leads": frappe.db.count("Lead"),
		"item_groups": frappe.db.count("Item Group"),
		"setup_complete": frappe.db.get_single_value("System Settings", "setup_complete"),
		"default_company": frappe.db.get_single_value("Global Defaults", "default_company"),
		"default_currency": frappe.db.get_single_value("Global Defaults", "default_currency"),
	}
	for k, v in out.items():
		print(f"OUT {k}: {v}")
	return out


def so_top_section():
	meta = frappe.get_meta("Sales Order")
	stop = False
	for df in meta.fields:
		if df.fieldtype in ("Tab Break",):
			if stop:
				break
			stop = True if df.fieldname != "details_tab" else False
			print(f"-- TAB BREAK: {df.fieldname}")
			if df.fieldname != "details_tab":
				break
		elif df.fieldtype in ("Section Break",):
			print(f"  -- SECTION: {df.fieldname} ({df.label or ''})")
		elif df.fieldtype == "Column Break":
			print(f"     -- COL BREAK: {df.fieldname}")
		else:
			hidden = " HIDDEN" if df.hidden else ""
			print(f"        {df.fieldname:30}  fieldtype={df.fieldtype:15} label={df.label or '':30}{hidden}")


def contact_columns():
	rows = frappe.db.sql("SHOW COLUMNS FROM `tabContact`", as_dict=True)
	for r in rows:
		print(f"COL {r['Field']}")


def fix_contact_is_billing():
	cf_name = "Contact-is_billing_contact"
	if not frappe.db.exists("Custom Field", cf_name):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Contact",
				"label": "Is Billing Contact",
				"fieldname": "is_billing_contact",
				"fieldtype": "Check",
				"insert_after": "is_primary_contact",
			}
		).insert(ignore_permissions=True)
		print("CF created")
	else:
		print("CF already exists")
	cols = {
		r["Field"]
		for r in frappe.db.sql("SHOW COLUMNS FROM `tabContact`", as_dict=True)
	}
	if "is_billing_contact" not in cols:
		frappe.db.sql_ddl(
			"ALTER TABLE `tabContact` ADD COLUMN `is_billing_contact` INT(1) NOT NULL DEFAULT 0"
		)
		print("Column added")
	else:
		print("Column already exists")
	frappe.db.commit()


def chart_preview():
	from frappe.desk.doctype.dashboard_chart.dashboard_chart import get
	for name in ("Earth Trading - Trades in MT", "Earth Trading - Trades By Item"):
		print(f"CHART: {name}")
		try:
			data = get(chart_name=name, refresh=1)
			print(f"  data: {data}")
		except Exception as e:
			print(f"  ERROR: {e}")


def trade_report_smoke():
	from earthentrading.earth_ent_trading.report.leads_by_trade_report.leads_by_trade_report import execute

	for label, filt in (
		("ALL", {}),
		("origin=Canada", {"origin": "Canada"}),
		("role=Buyer", {"role": "Buyer"}),
		("commodity contains 'Peas'", {"commodity": "Peas"}),
		("origin=Myanmar destination=India", {"origin": "Myanmar", "destination": "India"}),
	):
		cols, rows = execute(filt)
		print(f"FILT {label}: {len(rows)} rows")
		for r in rows[:5]:
			print(f"  -> {r['company_name']} | {r['tr_commodity']} | {r['tr_origin']}->{r['tr_destination']} ({r['tr_role']})")


def app_assets_report():
	hooks = frappe.get_hooks()
	for key in ("app_include_js", "app_include_css", "web_include_js", "web_include_css"):
		val = hooks.get(key)
		print(f"HOOK {key}: {val}")
