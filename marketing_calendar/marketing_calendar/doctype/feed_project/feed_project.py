# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from marketing_calendar.notifications import notify


class FeedProject(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.Text | None
		due_date: DF.Date | None
		priority: DF.Literal["High", "Medium", "Low"]
		project_owner: DF.Link
		stage: DF.Literal["Planning", "In Progress", "Review", "Done"]
		title: DF.Data
	# end: auto-generated types

	def before_insert(self):
		if not self.project_owner:
			self.project_owner = frappe.session.user

	def on_update(self):
		previous = self.get_doc_before_save()
		if not previous or previous.stage == self.stage:
			return
		notify(
			users=[self.project_owner],
			subject=frappe._("Project moved to {0}").format(self.stage),
			message=frappe._("{0} moved from {1} to {2}.").format(
				frappe.bold(self.title), previous.stage, self.stage
			),
			doc=self,
		)
