# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class MarketingPostTag(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		tag: DF.Data
	# end: auto-generated types
