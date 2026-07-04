import frappe


def execute():
    if frappe.db.exists("Module Def", "Marketing Calendar") and not frappe.db.exists("Module Def", "Feed"):
        frappe.rename_doc("Module Def", "Marketing Calendar", "Feed", ignore_permissions=True)
        frappe.db.commit()
