# Copyright (c) 2026, Foram Shah and contributors
# For license information, please see license.txt

"""Bakes EXIF orientation into pixel data on upload so photos display the
same way everywhere. Phone cameras store the "this way up" rotation as an
EXIF tag instead of rotating the actual pixels — most viewers respect that
tag, but browsers pulling the raw file into a <canvas> (which is exactly
what our compose/preview UI and Instagram's own ingestion do) don't, so the
same photo ends up right-side-up in some places and sideways in others.
Re-saving with the rotation applied to the pixels themselves and the tag
dropped makes orientation consistent no matter what reads the file next.
"""

import frappe

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif")


def fix_image_orientation(doc, method=None):
	if not doc.file_url or not doc.file_url.lower().endswith(IMAGE_EXTENSIONS):
		return

	try:
		from PIL import Image, ImageOps
	except ImportError:
		return

	try:
		path = doc.get_full_path()
		image = Image.open(path)
		oriented = ImageOps.exif_transpose(image)
		if oriented is None:
			return
		oriented.save(path, format=image.format)
	except Exception:
		frappe.log_error(title="Image orientation fix failed", message=frappe.get_traceback())
