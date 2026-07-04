"""
Rename all Marketing-prefixed DocTypes to Feed-prefixed names.
Runs in pre_model_sync so the new DocType JSON files (Feed Post, etc.)
are synced against the already-renamed DB records, not against stale ones.
"""

import frappe

RENAMES = [
    # Child tables first so their parenttype references get updated before
    # the parent rename touches any cascades.
    ("Marketing Post Platform", "Feed Post Platform"),
    ("Marketing Post Asset", "Feed Post Asset"),
    ("Marketing Post Tag", "Feed Post Tag"),
    # Parent DocTypes
    ("Marketing Post", "Feed Post"),
    ("Marketing Project", "Feed Project"),
    ("Marketing Task", "Feed Task"),
    ("Marketing Calendar Settings", "Feed Settings"),
    ("Marketing Social Account", "Feed Social Account"),
]

WORKFLOW_RENAME = ("Marketing Post Approval", "Feed Post Approval")


def execute():
    # ignore_permissions was removed in Frappe v16 — migration patches run as
    # Administrator so no permission flag is needed.
    for old, new in RENAMES:
        if frappe.db.exists("DocType", old) and not frappe.db.exists("DocType", new):
            frappe.rename_doc("DocType", old, new, force=True)
            frappe.db.commit()

    # Rename the workflow document
    old_wf, new_wf = WORKFLOW_RENAME
    if frappe.db.exists("Workflow", old_wf) and not frappe.db.exists("Workflow", new_wf):
        frappe.rename_doc("Workflow", old_wf, new_wf)
        frappe.db.commit()
