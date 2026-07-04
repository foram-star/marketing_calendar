# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

"""Scheduler entry point — without this, `scheduled_on` is just a label.
Runs as a background job (see `scheduler_events` in hooks.py), so it always
acts with the site's system privileges, the same way the "Publish now" button
does via `ignore_permissions=True` deeper in `run_publish`.
"""

import frappe

from marketing_calendar.api import run_publish


def publish_due_posts():
	due = frappe.get_all(
		"Feed Post",
		filters={"status": "Scheduled", "scheduled_on": ["<=", frappe.utils.now_datetime()]},
		pluck="name",
	)
	for name in due:
		try:
			doc = frappe.get_doc("Feed Post", name)
			run_publish(doc)
		except Exception:
			frappe.log_error(title=f"Scheduled publish failed for {name}")
		frappe.db.commit()
