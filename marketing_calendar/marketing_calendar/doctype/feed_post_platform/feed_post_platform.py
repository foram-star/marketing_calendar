# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class FeedPostPlatform(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		attempt_count: DF.Int
		blog_post: DF.Link | None
		caption: DF.Text | None
		error_message: DF.SmallText | None
		external_post_id: DF.Data | None
		external_url: DF.Data | None
		instagram_first_comment: DF.Text | None
		last_attempted_at: DF.Datetime | None
		link_url: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		platform: DF.Literal["LinkedIn", "X", "Instagram", "Blog"]
		published_at: DF.Datetime | None
		social_account: DF.Link | None
		status: DF.Literal["Pending", "Publishing", "Published", "Failed"]
		x_reply_settings: DF.Literal["Everyone", "Following", "Mentioned"]
		x_sensitive_media: DF.Check
	# end: auto-generated types
