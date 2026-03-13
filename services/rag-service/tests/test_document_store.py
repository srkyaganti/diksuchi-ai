"""
Tests for the document store module.

These tests verify the storage layer independently of Docling conversion,
using synthetic data. They cover:
  - Directory creation and file writing
  - JSON round-trip fidelity
  - Image write and retrieval
  - Path traversal rejection
  - Edge cases (missing documents, empty image sets)
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ["DOCLING_STORAGE_PATH"] = tempfile.mkdtemp(prefix="docstore_test_")

from src.storage.document_store import (
    document_exists,
    get_document,
    get_image_path,
    list_images,
    save_document,
)


SAMPLE_JSON = {
    "schema_name": "DoclingDocument",
    "version": "1.0.0",
    "name": "test-manual",
    "pages": {"1": {"page_no": 1, "size": {"width": 612, "height": 792}}},
    "texts": [
        {"self_ref": "#/texts/0", "text": "Chapter 1: Safety", "label": "section_header"},
        {"self_ref": "#/texts/1", "text": "Do not operate without guards.", "label": "paragraph"},
    ],
    "pictures": [
        {"self_ref": "#/pictures/0", "caption": "Hydraulic pump assembly"},
    ],
}

SAMPLE_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


class TestSaveAndReadDocument(unittest.TestCase):
    def setUp(self):
        self.uuid = "test-uuid-001"

    def test_save_creates_structure(self):
        doc_dir = save_document(
            self.uuid,
            docling_json=SAMPLE_JSON.copy(),
            images={"picture_1.png": SAMPLE_IMAGE},
            document_id=self.uuid,
        )
        self.assertTrue(doc_dir.exists())
        self.assertTrue((doc_dir / "document.json").exists())
        self.assertTrue((doc_dir / "images" / "picture_1.png").exists())

    def test_json_round_trip(self):
        original = SAMPLE_JSON.copy()
        save_document(self.uuid, original, images={})
        loaded = get_document(self.uuid)
        self.assertEqual(loaded["schema_name"], "DoclingDocument")
        self.assertEqual(loaded["texts"], SAMPLE_JSON["texts"])

    def test_document_id_injected(self):
        save_document(self.uuid, SAMPLE_JSON.copy(), images={}, document_id="my-id")
        loaded = get_document(self.uuid)
        self.assertEqual(loaded["document_id"], "my-id")

    def test_image_content_matches(self):
        save_document(self.uuid, SAMPLE_JSON.copy(), images={"img.png": SAMPLE_IMAGE})
        path = get_image_path(self.uuid, "img.png")
        self.assertIsNotNone(path)
        self.assertEqual(path.read_bytes(), SAMPLE_IMAGE)


class TestDocumentExists(unittest.TestCase):
    def test_exists_after_save(self):
        uuid = "exists-test"
        save_document(uuid, {"test": True}, images={})
        self.assertTrue(document_exists(uuid))

    def test_not_exists(self):
        self.assertFalse(document_exists("nonexistent-uuid"))


class TestListImages(unittest.TestCase):
    def test_list_multiple_images(self):
        uuid = "list-img-test"
        images = {
            "picture_1.png": SAMPLE_IMAGE,
            "picture_2.png": SAMPLE_IMAGE,
            "table_1.png": SAMPLE_IMAGE,
        }
        save_document(uuid, {"test": True}, images=images)
        result = list_images(uuid)
        self.assertEqual(result, ["picture_1.png", "picture_2.png", "table_1.png"])

    def test_list_empty(self):
        uuid = "no-images-test"
        save_document(uuid, {"test": True}, images={})
        result = list_images(uuid)
        self.assertEqual(result, [])

    def test_list_nonexistent_uuid(self):
        result = list_images("does-not-exist")
        self.assertEqual(result, [])


class TestGetImagePath(unittest.TestCase):
    def setUp(self):
        self.uuid = "imgpath-test"
        save_document(self.uuid, {"test": True}, images={"valid.png": SAMPLE_IMAGE})

    def test_valid_image(self):
        path = get_image_path(self.uuid, "valid.png")
        self.assertIsNotNone(path)
        self.assertTrue(path.exists())

    def test_missing_image(self):
        self.assertIsNone(get_image_path(self.uuid, "nope.png"))

    def test_path_traversal_rejected(self):
        self.assertIsNone(get_image_path(self.uuid, "../../../etc/passwd"))
        self.assertIsNone(get_image_path(self.uuid, "images/../secret"))
        self.assertIsNone(get_image_path(self.uuid, "sub/dir/file.png"))


class TestGetDocumentErrors(unittest.TestCase):
    def test_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            get_document("nonexistent-uuid-999")


if __name__ == "__main__":
    unittest.main()
