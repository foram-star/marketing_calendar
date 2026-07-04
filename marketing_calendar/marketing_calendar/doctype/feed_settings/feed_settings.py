# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

from urllib.parse import urljoin

import frappe
from frappe.model.document import Document

# Maps platform key -> whitelisted callback method that completes its OAuth flow.
CALLBACK_METHODS = {
	"meta": "marketing_calendar.api.oauth_callback_instagram",
	"linkedin": "marketing_calendar.api.oauth_callback_linkedin",
	"x": "marketing_calendar.api.oauth_callback_x",
}


class FeedSettings(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		linkedin_client_id: DF.Data | None
		linkedin_client_secret: DF.Password | None
		linkedin_redirect_uri: DF.Data | None
		meta_app_id: DF.Data | None
		meta_app_secret: DF.Password | None
		meta_redirect_uri: DF.Data | None
		meta_webhook_url: DF.Data | None
		meta_webhook_verify_token: DF.Data | None
		x_client_id: DF.Data | None
		x_client_secret: DF.Password | None
		x_redirect_uri: DF.Data | None
	# end: auto-generated types

	def validate(self):
		base_url = frappe.utils.get_url()
		for platform, method in CALLBACK_METHODS.items():
			self.set(f"{platform}_redirect_uri", urljoin(base_url, f"/api/method/{method}"))
		# Separate from the OAuth login redirect above — Meta's "Configure
		# webhooks" step (its own GET verification handshake + signed POST
		# events) is a different endpoint entirely.
		self.meta_webhook_url = urljoin(base_url, "/api/method/marketing_calendar.api.webhook_instagram")
