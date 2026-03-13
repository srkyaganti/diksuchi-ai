"""
Tests for the Docling converter module.

Mocks the Docling library at the module level so tests run without
installing the full Docling dependency. Verifies:
  - convert_pdf calls Docling correctly and returns the expected structure
  - Image extraction logic for PictureItem and TableItem
  - Error handling for missing files
"""

import io
import os
import sys
import tempfile
import types
import unittest
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create mock modules for docling before importing docling_converter
_mock_docling = types.ModuleType("docling")
_mock_dm_base = types.ModuleType("docling.datamodel.base_models")
_mock_dm_pipe = types.ModuleType("docling.datamodel.pipeline_options")
_mock_dm_doc = types.ModuleType("docling.document_converter")
_mock_core = types.ModuleType("docling_core")
_mock_core_types = types.ModuleType("docling_core.types")
_mock_core_doc = types.ModuleType("docling_core.types.doc")


class _FakePictureItem:
    pass


class _FakeTableItem:
    pass


_mock_dm_base.InputFormat = MagicMock()
_mock_dm_base.InputFormat.PDF = "PDF"
_mock_dm_pipe.PdfPipelineOptions = MagicMock
_mock_dm_doc.DocumentConverter = MagicMock
_mock_dm_doc.PdfFormatOption = MagicMock
_mock_core_doc.PictureItem = _FakePictureItem
_mock_core_doc.TableItem = _FakeTableItem

sys.modules["docling"] = _mock_docling
sys.modules["docling.datamodel"] = types.ModuleType("docling.datamodel")
sys.modules["docling.datamodel.base_models"] = _mock_dm_base
sys.modules["docling.datamodel.pipeline_options"] = _mock_dm_pipe
sys.modules["docling.document_converter"] = _mock_dm_doc
sys.modules["docling_core"] = _mock_core
sys.modules["docling_core.types"] = _mock_core_types
sys.modules["docling_core.types.doc"] = _mock_core_doc

from src.ingestion.docling_converter import DoclingResult, convert_pdf


class FakeImage:
    """Mimics a PIL Image for save() calls."""

    def __init__(self, data: bytes = b"FAKE_PNG"):
        self._data = data

    def save(self, fp: Any, format: str = "PNG") -> None:
        fp.write(self._data)


class FakeDoclingDocument:
    def __init__(self, elements, json_dict):
        self._elements = elements
        self._json_dict = json_dict

    def export_to_dict(self):
        return self._json_dict

    def iterate_items(self):
        return iter(self._elements)


class FakeConversionResult:
    def __init__(self, document):
        self.document = document


class TestConvertPdf(unittest.TestCase):
    def setUp(self):
        self.test_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.test_pdf.write(b"%PDF-1.4 fake content")
        self.test_pdf.close()

    def tearDown(self):
        os.unlink(self.test_pdf.name)

    def _make_pic(self, image_data: bytes = b"PIC_DATA"):
        pic = _FakePictureItem()
        pic.get_image = lambda doc: FakeImage(image_data)
        return pic

    def _make_table(self, image_data: bytes = b"TABLE_DATA"):
        table = _FakeTableItem()
        table.get_image = lambda doc: FakeImage(image_data)
        return table

    def _mock_converter(self, doc):
        import src.ingestion.docling_converter as mod

        conv_result = FakeConversionResult(document=doc)
        fake_converter = MagicMock()
        fake_converter.convert.return_value = conv_result
        mod._converter = fake_converter

    def test_basic_conversion(self):
        import src.ingestion.docling_converter as mod

        sample_json = {"schema_name": "DoclingDocument", "texts": []}
        pic = self._make_pic(b"PIC_DATA")
        table = self._make_table(b"TABLE_DATA")
        doc = FakeDoclingDocument(
            elements=[(pic, 0), (table, 0)], json_dict=sample_json
        )
        self._mock_converter(doc)

        result = convert_pdf(self.test_pdf.name)

        self.assertEqual(result.document_json, sample_json)
        self.assertIn("picture_1.png", result.images)
        self.assertIn("table_1.png", result.images)
        self.assertEqual(result.images["picture_1.png"], b"PIC_DATA")
        self.assertEqual(result.images["table_1.png"], b"TABLE_DATA")

    def test_no_images(self):
        doc = FakeDoclingDocument(elements=[], json_dict={"texts": []})
        self._mock_converter(doc)

        result = convert_pdf(self.test_pdf.name)
        self.assertEqual(result.images, {})

    def test_picture_with_none_image(self):
        pic = _FakePictureItem()
        pic.get_image = lambda doc: None
        doc = FakeDoclingDocument(elements=[(pic, 0)], json_dict={})
        self._mock_converter(doc)

        result = convert_pdf(self.test_pdf.name)
        self.assertEqual(result.images, {})

    def test_multiple_pictures(self):
        pics = [self._make_pic(f"DATA_{i}".encode()) for i in range(3)]
        doc = FakeDoclingDocument(
            elements=[(p, 0) for p in pics], json_dict={"n": 3}
        )
        self._mock_converter(doc)

        result = convert_pdf(self.test_pdf.name)
        self.assertEqual(len(result.images), 3)
        self.assertIn("picture_1.png", result.images)
        self.assertIn("picture_2.png", result.images)
        self.assertIn("picture_3.png", result.images)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            convert_pdf("/nonexistent/path/to/file.pdf")


class TestDoclingResult(unittest.TestCase):
    def test_dataclass_defaults(self):
        result = DoclingResult(document_json={"test": True})
        self.assertEqual(result.document_json, {"test": True})
        self.assertEqual(result.images, {})

    def test_with_images(self):
        result = DoclingResult(
            document_json={}, images={"a.png": b"data"}
        )
        self.assertEqual(result.images["a.png"], b"data")


if __name__ == "__main__":
    unittest.main()
