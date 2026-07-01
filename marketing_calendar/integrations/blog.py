# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

"""Blog connector — schedules an EXISTING `blog` app Blog Post, written and
owned entirely in the Blog app's own UI. The calendar never authors blog
content; it just flips `published` on the post you already picked once its
scheduled time arrives. No OAuth, no external app: real and testable without
any third-party credentials, unlike the social integrations.
"""

import frappe
from frappe import _


def publish(post, platform_row):
	if not frappe.db.exists("DocType", "Blog Post"):
		frappe.throw(_("The Blog app is not installed. Install frappe/blog to publish blog posts."))
	if not platform_row.blog_post:
		frappe.throw(_("Pick a blog post before publishing {0}.").format(post.title))
	if not frappe.db.exists("Blog Post", platform_row.blog_post):
		frappe.throw(_("{0} no longer exists in the Blog app.").format(platform_row.blog_post))

	blog_doc = frappe.get_doc("Blog Post", platform_row.blog_post)
	blog_doc.published = 1
	blog_doc.published_on = blog_doc.published_on or frappe.utils.today()
	blog_doc.save(ignore_permissions=True)

	platform_row.external_post_id = blog_doc.name
	platform_row.external_url = frappe.utils.get_url("/" + blog_doc.route) if blog_doc.route else None
	return platform_row
