# Copyright (c) 2026, Earth Trading and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ETLeadLine(Document):
	def validate(self):
		spec = (self.commodity or "").strip()
		if not self.item_code and not spec:
			frappe.throw(
				_("Select an Item or enter a short specification (grade, origin, enquiry text)."),
				title=_("Trading line"),
			)
