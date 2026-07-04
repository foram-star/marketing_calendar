# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

import frappe

no_cache = 1


def get_context(context):
	# Prevent nginx / CDN from caching this page — it's rendered per-request
	# and contains a CSRF token and session user.
	frappe.local.response["headers"] = {
		"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
		"Pragma": "no-cache",
	}

	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()  # nosemgrep

	context.boot = {
		"csrf_token": csrf_token,
		"user": frappe.session.user,
		"sitename": frappe.local.site,
		"is_guest": frappe.session.user == "Guest",
	}
