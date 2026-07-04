# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

import frappe
from frappe.desk.doctype.notification_log.notification_log import enqueue_create_notification

# Where each doctype's record opens inside the standalone /marketing SPA, so a
# notification clicked from Frappe's own bell icon still lands somewhere useful.
DEEP_LINK_ROUTES = {
	"Feed Post": "/marketing/posts/{name}",
	"Feed Project": "/marketing/projects/{name}",
	"Feed Task": "/marketing/todo?task={name}",
}


def notify(users: list[str], subject: str, message: str, doc) -> None:
	"""Notify `users` about `doc` via Frappe's standard Notification Log + realtime bell.

	`doc` is the triggering document (Feed Post / Feed Project, ...). This
	reuses `enqueue_create_notification`, the same helper Frappe uses for
	assignment/share/mention alerts, so entries show up in the normal bell icon
	(`after_insert` on Notification Log already does the `frappe.publish_realtime`
	for us) and our own SPA can read the same `Notification Log` list / socket
	event without a bespoke channel.
	"""
	user_ids = sorted({u for u in users if u and u != "Guest"})
	if not user_ids:
		return

	# `enqueue_create_notification` matches recipients by User.email (see
	# `_get_user_ids` in frappe/desk/doctype/notification_log/notification_log.py),
	# not by docname — those are the same for ordinary users but NOT for
	# Administrator, whose name and email differ. Resolve to email explicitly
	# so notifying Administrator (a real, valid assignee) actually works.
	emails = frappe.get_all("User", filters={"name": ["in", user_ids]}, pluck="email")
	if not emails:
		return

	route = DEEP_LINK_ROUTES.get(doc.doctype)
	link = route.format(name=doc.name) if route else None

	enqueue_create_notification(
		emails,
		{
			"type": "Alert",
			"document_type": doc.doctype,
			"document_name": doc.name,
			"subject": subject,
			"email_content": f"<p>{message}</p>",
			"from_user": frappe.session.user,
			"link": link,
		},
	)


def notify_duplicate_publish_blocked(post, platform_row) -> None:
	"""Raised when the scheduler and a manual 'Publish now' race on the same row."""
	users = [post.assigned_to]
	notify(
		users=users,
		subject=frappe._("Duplicate publish blocked"),
		message=frappe._(
			"A second attempt to publish {0} to {1} was blocked because it was already {2}."
		).format(frappe.bold(post.title), platform_row.platform, platform_row.status.lower()),
		doc=post,
	)
