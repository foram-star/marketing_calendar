# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class MarketingPostAsset(Document):
	# begin: auto-generated types
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		alt_text: DF.Data | None
		file: DF.Attach
		file_size: DF.Int
		file_type: DF.Literal["Image", "Video"]
		height: DF.Int
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		width: DF.Int
	# end: auto-generated types
