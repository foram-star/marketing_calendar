# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FeedTask(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		assigned_to: DF.Link | None
		description: DF.SmallText | None
		done: DF.Check
		marketing_project: DF.Link | None
		title: DF.Data
	# end: auto-generated types

	def before_insert(self):
		if not self.assigned_to:
			self.assigned_to = frappe.session.user
