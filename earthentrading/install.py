# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from earthentrading.setup.custom_fields import CUSTOM_FIELDS
from earthentrading.setup.field_order import ensure_sales_order_field_order
from earthentrading.setup.dashboard import ensure_earth_trading_dashboard
from earthentrading.setup.lead_functions import ensure_lead_functions
from earthentrading.setup.lead_layout import apply_lead_layout
from earthentrading.setup.ports import ensure_ports
from earthentrading.setup.payment_terms import ensure_payment_terms_templates
from earthentrading.setup.property_setters import ensure_property_setters
from earthentrading.setup.roles import ensure_role_permissions, ensure_roles
from earthentrading.setup.crm_workspace import (
	ensure_earth_trading_workspace,
	refresh_web_form_incoterm,
)
from earthentrading.setup.selling_workspace import ensure_selling_workspace
from earthentrading.setup.sidebar_cleanup import trim_public_sidebar
from earthentrading.setup.kanban import ensure_lead_pipeline_kanban
from earthentrading.setup.task_templates import ensure_task_templates
from earthentrading.setup.migrate_trading_lines import run_all as migrate_trading_lines_data
from earthentrading.setup.web_form import ensure_lead_web_form, sync_earth_trading_lead_web_form
from earthentrading.setup.workflow import ensure_workflows
from earthentrading.setup.migrate_workflow_state_names import rename_legacy_workflow_states


def before_install():
	if "erpnext" not in frappe.get_installed_apps():
		frappe.throw("Earth Trading requires ERPNext to be installed on the site.")


def after_install():
	_install_all()


def after_migrate():
	_install_all()


def _install_all():
	create_custom_fields(CUSTOM_FIELDS, update=True)
	try:
		ensure_sales_order_field_order()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_sales_order_field_order")
	try:
		ensure_property_setters()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_property_setters")
	try:
		apply_lead_layout()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.apply_lead_layout")
	try:
		ensure_lead_functions()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_lead_functions")
	try:
		ensure_ports()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_ports")
	try:
		ensure_payment_terms_templates()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_payment_terms_templates")
	try:
		migrate_trading_lines_data()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.migrate_trading_lines_data")
	ensure_roles()
	ensure_role_permissions()
	try:
		ensure_workflows()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_workflows")
	try:
		rename_legacy_workflow_states()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.rename_legacy_workflow_states")
	try:
		ensure_lead_web_form()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_lead_web_form")
	try:
		sync_earth_trading_lead_web_form()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.sync_earth_trading_lead_web_form")
	try:
		ensure_task_templates()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_task_templates")
	try:
		ensure_lead_pipeline_kanban()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_lead_pipeline_kanban")
	try:
		refresh_web_form_incoterm()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.refresh_web_form_incoterm")
	try:
		ensure_earth_trading_workspace()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_earth_trading_workspace")
	try:
		ensure_earth_trading_dashboard()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_earth_trading_dashboard")
	try:
		ensure_selling_workspace()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.ensure_selling_workspace")
	try:
		trim_public_sidebar()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "earthentrading.trim_public_sidebar")
	frappe.clear_cache()
