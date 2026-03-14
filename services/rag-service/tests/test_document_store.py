"""
Tests for the document store module.

Verifies the storage layer independently of Docling conversion,
using synthetic data. Covers:
  - Directory creation and file writing (markdown + section map)
  - Markdown round-trip fidelity
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

import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.document_store import (
    document_exists,
    get_markdown,
    get_section_map,
    get_image_path,
    list_images,
    save_document,
)


SAMPLE_MARKDOWN = """# Chapter 1: Safety

Do not operate without guards.

## 1.1 Warnings

Always wear protective equipment.
"""

SAMPLE_SECTION_MAP = {
    "sections": [
        {
            "id": "section-1",
            "title": "Chapter 1: Safety",
            "level": 1,
            "path": "Chapter 1: Safety",
            "start_line": 0,
            "end_line": 6,
            "children": [
                {
                    "id": "section-2",
                    "title": "1.1 Warnings",
                    "level": 2,
                    "path": "Chapter 1: Safety > 1.1 Warnings",
                    "start_line": 4,
                    "end_line": 6,
                    "children": [],
                }
            ],
        }
    ]
}

SAMPLE_IMAGE = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100


class TestSaveAndReadDocument(unittest.TestCase):
    def setUp(self):
        self.uuid = "test-uuid-001"

    def test_save_creates_structure(self):
        doc_dir = save_document(
            self.uuid,
            markdown=SAMPLE_MARKDOWN,
            images={"picture_1.png": SAMPLE_IMAGE},
            section_map=SAMPLE_SECTION_MAP,
            document_id=self.uuid,
        )
        self.assertTrue(doc_dir.exists())
        self.assertTrue((doc_dir / "document.md").exists())
        self.assertTrue((doc_dir / "section_map.json").exists())
        self.assertTrue((doc_dir / "images" / "picture_1.png").exists())

    def test_markdown_round_trip(self):
        save_document(self.uuid, markdown=SAMPLE_MARKDOWN, images={})
        loaded = get_markdown(self.uuid)
        self.assertEqual(loaded, SAMPLE_MARKDOWN)

    def test_section_map_round_trip(self):
        save_document(
            self.uuid,
            markdown=SAMPLE_MARKDOWN,
            images={},
            section_map=SAMPLE_SECTION_MAP,
            document_id="my-id",
        )
        loaded = get_section_map(self.uuid)
        self.assertEqual(loaded["document_id"], "my-id")
        self.assertEqual(len(loaded["sections"]), 1)
        self.assertEqual(loaded["sections"][0]["title"], "Chapter 1: Safety")

    def test_image_content_matches(self):
        save_document(self.uuid, markdown="# Test", images={"img.png": SAMPLE_IMAGE})
        path = get_image_path(self.uuid, "img.png")
        self.assertIsNotNone(path)
        self.assertEqual(path.read_bytes(), SAMPLE_IMAGE)


class TestDocumentExists(unittest.TestCase):
    def test_exists_after_save(self):
        uuid = "exists-test"
        save_document(uuid, markdown="# Exists", images={})
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
        save_document(uuid, markdown="# Images", images=images)
        result = list_images(uuid)
        self.assertEqual(result, ["picture_1.png", "picture_2.png", "table_1.png"])

    def test_list_empty(self):
        uuid = "no-images-test"
        save_document(uuid, markdown="# No images", images={})
        result = list_images(uuid)
        self.assertEqual(result, [])

    def test_list_nonexistent_uuid(self):
        result = list_images("does-not-exist")
        self.assertEqual(result, [])


class TestGetImagePath(unittest.TestCase):
    def setUp(self):
        self.uuid = "imgpath-test"
        save_document(self.uuid, markdown="# Test", images={"valid.png": SAMPLE_IMAGE})

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


class TestGetMarkdownErrors(unittest.TestCase):
    def test_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            get_markdown("nonexistent-uuid-999")


if __name__ == "__main__":
    unittest.main()
