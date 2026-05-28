# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Seed ET Task Template documents from trading / brokerage checklists."""

import frappe

# (template_code, title, ordered task titles) — granular task list matching the
# Operations Task view (CRM screenshot).
BROKERAGE_TASKS = [
	"BC Review",
	"Compliance Check",
	"History Review",
	"Regulations Review",
	"Know Your Counterparty (Internal)",
	"KYC (External)",
	"Contract Issuance",
	"Contract Review",
	"Contract Signature",
	"Service Agreement",
	"Bank Details Review",
	"Down Payment",
	"Final LC",
	"Confirm OBL or Telex",
	"Tags & Shipping Instructions",
	"Import Permit",
	"Booking Confirmation",
	"Free Days Confirmation",
	"Confirm Departure",
	"Appropriation or BL",
	"Documents Issuance",
	"QA Review",
	"Documents Review",
	"Documents Amendments",
	"Documents Approval",
	"Delivery Note",
	"Balance Payment",
	"Documents Release",
	"Sales Invoice",
	"Insurance Claim",
	"Quality Claim",
	"D&D / S Claim",
]


TRADING_DIRECT_B2B_TASKS = [
	"PO Review",
	"BC Review",
	"Compliance Check",
	"History Review",
	"Regulations Review",
	"Know Your Counterparty (Internal)",
	"KYC (External)",
	"Contract Issuance with Seller",
	"Contract Issuance with Buyer",
	"Contract Review",
	"Contract Signature",
	"Bank Details Review",
	"Down Payment to Seller",
	"Down Payment from Buyer",
	"Letter of Credit to Seller",
	"Letter of Credit from Buyer",
	"Tags & Shipping Instructions",
	"Import Permit",
	"Booking Confirmation",
	"Free Days Confirmation",
	"Confirm Departure",
	"Appropriation or BL",
	"Documents Issuance from Seller",
	"Documents Issuance to Buyer",
	"QA Review",
	"Documents Review",
	"Documents Amendments",
	"Documents Approval",
	"Delivery Note",
	"Balance Payment from Buyer",
	"Balance Payment to Seller",
	"Documents Release",
	"Sales Invoice",
	"Insurance Claim",
	"Quality Claim",
	"D&D / S Claim",
]


TRADING_TO_SELLER_TASKS = [
	"PO Review",
	"Compliance Check",
	"History Review",
	"Regulations Review",
	"Know Your Counterparty (Internal)",
	"KYC (External)",
	"Contract Issuance",
	"Contract Review",
	"Contract Signature",
	"Bank Details Review",
	"Down Payment",
	"Letter of Credit to Seller",
	"Tags & Shipping Instructions to Seller / Processor",
	"Tags & Shipping Instructions to Forwarder",
	"Import Permit",
	"Booking Confirmation",
	"Free Days Confirmation",
	"Loading Report from Seller / Processor",
	"Delivery Note",
	"Documents Issuance",
	"Sample Submission Form – Phyto Application",
	"QA Review",
	"Documents Review",
	"Documents Amendments",
	"Documents Approval",
	"Insurance",
	"Confirm Departure",
	"Appropriation or BL",
	"Balance Payment from Buyer",
	"Balance Payment to Seller / Processor",
	"Payment to Forwarder",
	"Documents Release",
	"Sales Invoice",
	"Insurance Claim",
	"Quality Claim",
	"D&D / S Claim",
]


TRADING_TO_BUYER_TASKS = [
	"BC Review",
	"Compliance Check",
	"History Review",
	"Regulations Review",
	"Know Your Counterparty (Internal)",
	"KYC (External)",
	"Contract Issuance",
	"Contract Review",
	"Contract Signature",
	"Service Agreement",
	"Bank Details Review",
	"Down Payment",
	"Final LC",
	"Confirm OBL or Telex",
	"Tags & Shipping Instructions",
	"Import Permit",
	"Booking Confirmation",
	"Free Days Confirmation",
	"Confirm Departure",
	"Appropriation or BL",
	"Documents Issuance",
	"QA Review",
	"Documents Review",
	"Documents Amendments",
	"Documents Approval",
	"Delivery Note",
	"Balance Payment",
	"Documents Release",
	"Sales Invoice",
	"Insurance Claim",
	"Quality Claim",
	"D&D / S Claim",
]


TEMPLATE_DEFS = [
	("brokerage", "Brokerage", BROKERAGE_TASKS),
	("trading_direct_b2b", "Trading – Direct (Back to Back)", TRADING_DIRECT_B2B_TASKS),
	("trading_to_seller", "Trading – To Seller (Stock or Exw or FOB)", TRADING_TO_SELLER_TASKS),
	("trading_to_buyer", "Trading – To Buyer", TRADING_TO_BUYER_TASKS),
]


def ensure_task_templates():
	if not frappe.db.exists("DocType", "ET Task Template"):
		return

	for code, title, task_titles in TEMPLATE_DEFS:
		if frappe.db.exists("ET Task Template", code):
			doc = frappe.get_doc("ET Task Template", code)
		else:
			doc = frappe.new_doc("ET Task Template")
			doc.template_code = code

		doc.title = title
		doc.tasks = []
		for idx, task_title in enumerate(task_titles, start=1):
			doc.append("tasks", {"task_title": task_title, "idx": idx})

		if doc.is_new():
			doc.insert(ignore_permissions=True)
		else:
			doc.save(ignore_permissions=True)

	frappe.db.commit()
