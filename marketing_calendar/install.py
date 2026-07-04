# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

import frappe

ROLES = ["Marketing Manager", "Marketing User"]

WORKFLOW_NAME = "Feed Post Approval"

# Pending/Approved/Rejected and Approve/Reject/Review already exist as Frappe
# defaults; everything else here is new and needs to be created once.
WORKFLOW_STATES = [
	"Draft",
	"In Review",
	"Approved",
	"Rejected",
	"Scheduled",
	"Published",
	"Partially Published",
	"Failed",
]
WORKFLOW_ACTIONS = [
	"Submit for Review",
	"Approve",
	"Reject",
	"Withdraw",
	"Revise",
	"Schedule",
	"Unschedule",
	"Mark Published",
	"Mark Partially Published",
	"Mark Failed",
	"Retry",
]

BOTH_ROLES = ["Marketing User", "Marketing Manager"]

# (state, action, next_state, allowed roles, condition, allow_self_approval)
TRANSITIONS = [
	("Draft", "Submit for Review", "In Review", BOTH_ROLES, None, False),
	("In Review", "Approve", "Approved", ["Marketing Manager"], None, True),
	("In Review", "Reject", "Rejected", ["Marketing Manager"], None, True),
	("In Review", "Withdraw", "Draft", BOTH_ROLES, None, False),
	("Rejected", "Revise", "Draft", BOTH_ROLES, None, False),
	("Approved", "Schedule", "Scheduled", BOTH_ROLES, "doc.scheduled_on", False),
	("Scheduled", "Unschedule", "Approved", BOTH_ROLES, None, False),
	# These three are driven by the publish job (runs as Administrator, which
	# has every role) rather than by a human clicking a button.
	("Scheduled", "Mark Published", "Published", ["Marketing Manager"], None, False),
	("Scheduled", "Mark Partially Published", "Partially Published", ["Marketing Manager"], None, False),
	("Scheduled", "Mark Failed", "Failed", ["Marketing Manager"], None, False),
	("Failed", "Retry", "Scheduled", BOTH_ROLES, None, False),
]


def after_install():
	create_roles()
	create_workflow()


def after_migrate():
	_copy_frontend_assets()
	frappe.clear_cache()


def _copy_frontend_assets():
	"""
	Explicitly copy public/frontend/ to the site's assets directory.

	bench build copies app public files, but on Frappe Cloud the build step
	sometimes doesn't re-copy files when only pre-built assets changed in git.
	Running this on every migrate guarantees the site always serves the JS/CSS
	that matches the currently-deployed commit, with no manual intervention.
	"""
	import os
	import shutil

	src = frappe.get_app_path("marketing_calendar", "public", "frontend")
	dst = os.path.join(
		frappe.get_site_path(), "public", "assets", "marketing_calendar", "frontend"
	)
	if os.path.isdir(src):
		os.makedirs(dst, exist_ok=True)
		shutil.copytree(src, dst, dirs_exist_ok=True)
		frappe.logger().info(f"Feed: copied frontend assets from {src} to {dst}")


def create_roles():
	for role in ROLES:
		if frappe.db.exists("Role", role):
			continue
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role,
				"desk_access": 1,
			}
		).insert(ignore_permissions=True)
	frappe.db.commit()


def create_workflow():
	_ensure_masters("Workflow State", "workflow_state_name", WORKFLOW_STATES)
	_ensure_masters("Workflow Action Master", "workflow_action_name", WORKFLOW_ACTIONS)

	if frappe.db.exists("Workflow", WORKFLOW_NAME):
		frappe.db.commit()
		return

	transitions = []
	for state, action, next_state, roles, condition, allow_self in TRANSITIONS:
		for role in roles:
			row = {"state": state, "action": action, "next_state": next_state, "allowed": role}
			if condition:
				row["condition"] = condition
			if allow_self:
				row["allow_self_approval"] = 1
			transitions.append(row)

	# `allow_edit` only affects Desk's own form rendering (frappe/public/js/frappe/model/workflow.js) —
	# our SPA doesn't load that JS, so this is cosmetic-for-Desk-only, not a real permission gate.
	edit_role_by_state = {
		"Draft": "Marketing User",
		"Rejected": "Marketing User",
	}
	frappe.get_doc(
		{
			"doctype": "Workflow",
			"workflow_name": WORKFLOW_NAME,
			"document_type": "Feed Post",
			"workflow_state_field": "status",
			"is_active": 1,
			"send_email_alert": 0,
			"states": [
				{
					"state": s,
					"doc_status": "0",
					"allow_edit": edit_role_by_state.get(s, "Marketing Manager"),
				}
				for s in WORKFLOW_STATES
			],
			"transitions": transitions,
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()


def _ensure_masters(doctype, fieldname, values):
	for value in values:
		if frappe.db.exists(doctype, value):
			continue
		frappe.get_doc({"doctype": doctype, fieldname: value}).insert(ignore_permissions=True)
