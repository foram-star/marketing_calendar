# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from marketing_calendar.notifications import notify

# Statuses that imply the post is committed to going out and therefore must
# already have at least one platform (with its own caption filled in) and,
# for Scheduled, a publish time. Enforced here in addition to the Workflow's
# own "Schedule" transition condition, since validate() also runs on plain saves.
COMMITTED_STATUSES = {"Approved", "Scheduled", "Published", "Partially Published"}

# Notified beyond the reviewer-on-submit case below — covers every outcome a
# human or the publish job can land a post on.
NOTIFY_ON_STATUS = {"Approved", "Rejected", "Published", "Partially Published", "Failed"}

# Mirrors the limits shown client-side (src/data/platforms.js) — re-checked
# here because the client-side counter is just a courtesy; nothing stops a
# direct API call or a stale UI from submitting something over-limit, and an
# over-limit caption would otherwise only be caught by the platform's own API
# at publish time, with a far less useful error.
PLATFORM_CAPTION_LIMITS = {"LinkedIn": 3000, "X": 280, "Instagram": 2200}


class FeedPost(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from marketing_calendar.marketing_calendar.doctype.feed_post_asset.feed_post_asset import (
			MarketingPostAsset,
		)
		from marketing_calendar.marketing_calendar.doctype.feed_post_platform.feed_post_platform import (
			MarketingPostPlatform,
		)
		from marketing_calendar.marketing_calendar.doctype.feed_post_tag.feed_post_tag import (
			MarketingPostTag,
		)

		assets: DF.Table[MarketingPostAsset]
		assigned_to: DF.Link | None
		marketing_task: DF.Link | None
		platforms: DF.Table[MarketingPostPlatform]
		reviewer: DF.Link | None
		scheduled_on: DF.Datetime | None
		status: DF.Literal[
			"Draft",
			"In Review",
			"Approved",
			"Rejected",
			"Scheduled",
			"Published",
			"Partially Published",
			"Failed",
		]
		tags: DF.Table[MarketingPostTag]
		title: DF.Data
	# end: auto-generated types

	def before_insert(self):
		if not self.assigned_to:
			self.assigned_to = frappe.session.user

	def validate(self):
		if self.status in COMMITTED_STATUSES:
			if not self.platforms:
				frappe.throw(_("Pick at least one platform before moving this post to {0}.").format(self.status))
			for row in self.platforms:
				if row.platform == "Blog":
					if not row.blog_post:
						frappe.throw(_("Pick a blog post before moving this post to {0}.").format(self.status))
					continue
				if not row.caption:
					frappe.throw(_("Add a caption for {0} before moving this post to {1}.").format(row.platform, self.status))
				limit = PLATFORM_CAPTION_LIMITS.get(row.platform)
				if limit and len(row.caption) > limit:
					frappe.throw(
						_("{0}'s caption is {1} characters over its {2}-character limit.").format(
							row.platform, len(row.caption) - limit, limit
						)
					)
				if row.platform == "Instagram" and not self.assets:
					frappe.throw(_("Instagram requires at least one image or video — it can't publish a text-only post."))
		if self.status == "Scheduled" and not self.scheduled_on:
			frappe.throw(_("Set a publish date & time before scheduling this post."))

	def on_update(self):
		previous = self.get_doc_before_save()
		if not previous or previous.status == self.status:
			return

		recipients = []
		if self.status == "In Review":
			recipients = [self.reviewer]
		elif self.status in NOTIFY_ON_STATUS:
			recipients = [self.assigned_to, self.reviewer]

		notify(
			users=recipients,
			subject=_("{0} is now {1}").format(self.title, self.status),
			message=_("{0} moved from {1} to {2}.").format(
				frappe.bold(self.title), previous.status, self.status
			),
			doc=self,
		)
