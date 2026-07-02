# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

import frappe

no_cache = 1


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()  # nosemgrep

	context.boot = {
		"csrf_token": csrf_token,
		"user": frappe.session.user,
		"sitename": frappe.local.site,
		"is_guest": frappe.session.user == "Guest",
	}
