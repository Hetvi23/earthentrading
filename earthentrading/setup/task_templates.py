# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Seed ET Task Template documents from trading / brokerage checklists."""

import frappe

# (template_code, title, ordered task titles) — aligned with List of tasks.xlsx tabs
TEMPLATE_DEFS = [
	(
		"brokerage",
		"Brokerage",
		[
			"BC Review",
			"Compliance, History, Regulation check",
			"Contact",
			"KYC",
			"Contract",
			"Brokerage contract",
			"Bank details review",
			"Down Payment",
			"Letter of Credit",
			"Bag Marking, Packing",
			"Shipping Instructions",
			"Import Permit",
			"Booking Confirmation",
			"Free Days Confirmation",
			"Confirm Departure",
			"Draft documents",
			"QA review",
			"Final documents",
			"Delivery Note",
			"Balance payment",
			"Documents release",
			"Commission Invoice",
			"Claim",
		],
	),
	(
		"trading_direct_b2b",
		"Trading – Direct (Back to Back)",
		[
			"PO Review",
			"BC Review",
			"Compliance, History, Regulation check",
			"Contact",
			"KYC",
			"Contract with Seller",
			"Contract with Buyer",
			"Bank details review",
			"Down Payment to Seller",
			"Down Payment to Buyer",
			"Letter of Credit to Seller",
			"Letter of Credit to Buyer",
			"Bag Marking, Packing",
			"Shipping Instructions",
			"Import Permit",
			"Booking Confirmation",
			"Free Days Confirmation",
			"Confirm Departure",
			"Draft documents from Seller",
			"Draft documents to Buyer",
			"QA review",
			"Final documents from Seller",
			"Final documents to Buyer",
			"Delivery Note",
			"Balance payment from Buyer",
			"Balance payment to Seller",
			"Documents release",
			"Claim",
		],
	),
	(
		"trading_to_seller",
		"Trading – To Seller (Stock or Exw or FOB)",
		[
			"PO Review",
			"Compliance, History, Regulation check",
			"Contact",
			"KYC",
			"Contract",
			"Bank details review",
			"Down Payment",
			"Letter of Credit to Seller",
			"Bag Marking, Packing, SI to Seller/ Processor",
			"Bag Marking, Packing, SI to Forwarder",
			"Import Permit",
			"Booking Confirmation",
			"Free Days Confirmation",
			"Loading report from Seller/ Processor",
			"Delivery Note",
			"Documents Issuance",
			"Sample Submission Form - Phyto Application",
			"QA review",
			"Documents review",
			"Insurance",
			"Confirm Departure",
			"Final documents",
			"Balance payment from Buyer",
			"Balance payment to Seller/ Processor",
			"Payment to Forwarder",
			"Documents release",
			"Claim",
		],
	),
	(
		"trading_to_buyer",
		"Trading – To Buyer",
		[
			"BC Review",
			"Compliance, History, Regulation check",
			"Contact",
			"KYC",
			"Contract",
			"Brokerage contract",
			"Bank details review",
			"Down Payment",
			"Letter of Credit",
			"Bag Marking, Packing",
			"Shipping Instructions",
			"Import Permit",
			"Booking Confirmation",
			"Free Days Confirmation",
			"Confirm Departure",
			"Draft documents",
			"QA review",
			"Final documents",
			"Delivery Note",
			"Balance payment",
			"Documents release",
			"Commission Invoice",
			"Claim",
		],
	),
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
