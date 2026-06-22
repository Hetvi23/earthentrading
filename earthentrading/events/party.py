# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

"""Customer / Supplier hooks: turn the quick-add 'one email per line' box into
rows in the custom_et_emails table.

The Emails table (ET Party Email) is the real store — multiple addresses per
party, each flaggable as Primary (the 'To' on trade confirmations); the rest are
CC'd. A child table can't be shown in Frappe's quick-entry popup, so the
Small Text box `custom_et_emails_quick` lets the user paste several addresses on
create; this parses them into the table and clears the box.
"""

import frappe
from frappe import _
from frappe.utils import validate_email_address


def sync_party_emails(doc, method=None):
	raw = (doc.get("custom_et_emails_quick") or "").strip()
	if not raw:
		return

	existing = {(r.email or "").strip().lower() for r in (doc.get("custom_et_emails") or [])}
	has_primary = any(r.is_primary for r in (doc.get("custom_et_emails") or []))

	skipped: list[str] = []
	for chunk in raw.replace(",", "\n").replace(";", "\n").splitlines():
		addr = chunk.strip()
		if not addr:
			continue
		cleaned = validate_email_address(addr, throw=False)
		if not cleaned:
			skipped.append(addr)
			continue
		if cleaned.lower() in existing:
			continue
		existing.add(cleaned.lower())
		is_primary = 0
		if not has_primary:
			is_primary = 1
			has_primary = True
		doc.append("custom_et_emails", {"email": cleaned, "is_primary": is_primary})

	# Clear the quick-add box so it doesn't re-append on the next save.
	doc.custom_et_emails_quick = None

	if skipped:
		frappe.msgprint(
			_("Skipped invalid email address(es): {0}").format(", ".join(skipped)),
			title=_("Earth Trading"),
			indicator="orange",
		)
