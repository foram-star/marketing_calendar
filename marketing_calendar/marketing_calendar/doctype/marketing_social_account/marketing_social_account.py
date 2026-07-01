# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MarketingSocialAccount(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		access_token: DF.Password | None
		account_label: DF.Data
		enabled: DF.Check
		external_account_id: DF.Data | None
		external_username: DF.Data | None
		last_error: DF.SmallText | None
		last_synced_on: DF.Datetime | None
		meta_page_id: DF.Data | None
		platform: DF.Literal["LinkedIn", "X", "Instagram"]
		refresh_token: DF.Password | None
		status: DF.Literal["Not Connected", "Connected", "Token Expired", "Error"]
		token_expires_on: DF.Datetime | None
	# end: auto-generated types

	def before_save(self):
		if self.access_token and self.status == "Not Connected":
			self.status = "Connected"

	def mark_error(self, message: str):
		self.status = "Error"
		self.last_error = message
		self.save(ignore_permissions=True)
		frappe.db.commit()
