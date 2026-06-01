# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Seed default ET Port rows (commonly-used international trading ports)."""

import frappe

# (port_name, country)
DEFAULT_PORTS = [
	# India
	("Nhava Sheva", "India"),
	("Mundra", "India"),
	("Chennai", "India"),
	("Kolkata", "India"),
	("Tuticorin", "India"),
	("Cochin", "India"),
	("Visakhapatnam", "India"),
	# East / SE Asia
	("Singapore", "Singapore"),
	("Ho Chi Minh", "Vietnam"),
	("Haiphong", "Vietnam"),
	("Bangkok", "Thailand"),
	("Laem Chabang", "Thailand"),
	("Yangon", "Myanmar"),
	("Chittagong", "Bangladesh"),
	("Dhaka", "Bangladesh"),
	("Colombo", "Sri Lanka"),
	("Hambantota", "Sri Lanka"),
	# Middle East / Africa
	("Jebel Ali", "United Arab Emirates"),
	("Sharjah", "United Arab Emirates"),
	("Lagos", "Nigeria"),
	("Apapa", "Nigeria"),
	("Port Sudan", "Sudan"),
	("Khartoum", "Sudan"),
	("Dar es Salaam", "Tanzania"),
	("Tanga", "Tanzania"),
	# Americas
	("Vancouver", "Canada"),
	("Halifax", "Canada"),
	("Los Angeles", "United States"),
	("New York", "United States"),
	("Santos", "Brazil"),
	("Paranagua", "Brazil"),
	# Australia
	("Melbourne", "Australia"),
	("Sydney", "Australia"),
	# Russia / others
	("Novorossiysk", "Russia"),
	("St Petersburg", "Russia"),
]


def ensure_ports():
	if not frappe.db.exists("DocType", "ET Port"):
		return
	for port_name, country in DEFAULT_PORTS:
		if frappe.db.exists("ET Port", port_name):
			continue
		country_value = country if frappe.db.exists("Country", country) else None
		frappe.get_doc(
			{
				"doctype": "ET Port",
				"port_name": port_name,
				"country": country_value,
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()
