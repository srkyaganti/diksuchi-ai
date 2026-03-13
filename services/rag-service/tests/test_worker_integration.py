"""
Integration tests for the document processing worker.

Mocks external dependencies (docling, dotenv, rq, redis, httpx) at the
module level so tests run without installing the full dependency set.
"""

import os
import sys
import tempfile
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["DOCLING_STORAGE_PATH"] = tempfile.mkdtemp(prefix="worker_test_")

# Mock external dependencies that may not be installed locally
for mod_name in [
    "dotenv",
    "httpx",
    "rq",
    "rq.worker",
    "redis",
    "docling",
    "docling.datamodel",
    "docling.datamodel.base_models",
    "docling.datamodel.pipeline_options",
    "docling.document_converter",
    "docling_core",
    "docling_core.types",
    "docling_core.types.doc",
]:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = types.ModuleType(mod_name)

sys.modules["dotenv"].load_dotenv = lambda: None
sys.modules["rq"].get_current_job = lambda: None

fake_redis = MagicMock()
sys.modules["redis"].Redis = MagicMock(return_value=fake_redis)

sys.modules["docling.datamodel.base_models"].InputFormat = MagicMock()
sys.modules["docling.datamodel.pipeline_options"].PdfPipelineOptions = MagicMock
sys.modules["docling.document_converter"].DocumentConverter = MagicMock
sys.modules["docling.document_converter"].PdfFormatOption = MagicMock
sys.modules["docling_core.types.doc"].PictureItem = type("PictureItem", (), {})
sys.modules["docling_core.types.doc"].TableItem = type("TableItem", (), {})

# Now we can import the worker
from src.ingestion.docling_converter import DoclingResult
import worker


class TestProcessDocumentJob(unittest.TestCase):
    def setUp(self):
        self.test_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.test_pdf.write(b"%PDF-1.4 fake content")
        self.test_pdf.close()

        self.job_data = {
            "fileId": "file-001",
            "collectionId": "coll-001",
            "fileName": "manual.pdf",
            "filePath": self.test_pdf.name,
            "mimeType": "application/pdf",
            "uuid": "test-worker-uuid",
        }

    def tearDown(self):
        os.unlink(self.test_pdf.name)

    @patch.object(worker, "update_file_status", new_callable=AsyncMock)
    @patch.object(worker, "update_job_progress")
    @patch.object(worker, "convert_pdf")
    @patch.object(worker, "save_document")
    def test_successful_processing(
        self, mock_save, mock_convert, mock_progress, mock_status
    ):
        mock_convert.return_value = DoclingResult(
            document_json={"schema_name": "DoclingDocument"},
            images={"picture_1.png": b"PNG_DATA"},
        )

        result = worker.process_document_job(self.job_data)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["fileId"], "file-001")
        self.assertEqual(result["uuid"], "test-worker-uuid")
        self.assertIn("processedAt", result)

        mock_convert.assert_called_once_with(self.test_pdf.name)
        mock_save.assert_called_once()
        call_kwargs = mock_save.call_args.kwargs
        self.assertEqual(call_kwargs["uuid"], "test-worker-uuid")
        self.assertEqual(call_kwargs["document_id"], "test-worker-uuid")

    @patch.object(worker, "update_file_status", new_callable=AsyncMock)
    @patch.object(worker, "update_job_progress")
    def test_missing_file_raises(self, mock_progress, mock_status):
        bad_data = self.job_data.copy()
        bad_data["filePath"] = "/nonexistent/path.pdf"

        with self.assertRaises(FileNotFoundError):
            worker.process_document_job(bad_data)

    @patch.object(worker, "update_file_status", new_callable=AsyncMock)
    @patch.object(worker, "update_job_progress")
    def test_unsupported_mime_type_raises(self, mock_progress, mock_status):
        txt_file = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        txt_file.write(b"not a pdf")
        txt_file.close()

        try:
            bad_data = self.job_data.copy()
            bad_data["mimeType"] = "application/zip"
            bad_data["filePath"] = txt_file.name

            with self.assertRaises(ValueError):
                worker.process_document_job(bad_data)
        finally:
            os.unlink(txt_file.name)

    @patch.object(worker, "update_file_status", new_callable=AsyncMock)
    @patch.object(worker, "update_job_progress")
    @patch.object(worker, "convert_pdf")
    def test_conversion_failure_reports_error(
        self, mock_convert, mock_progress, mock_status
    ):
        mock_convert.side_effect = RuntimeError("Docling crashed")

        with self.assertRaises(RuntimeError):
            worker.process_document_job(self.job_data)

        # Last status call should be "failed"
        last_status_call = mock_status.call_args_list[-1]
        self.assertEqual(last_status_call.args[1], "failed")


if __name__ == "__main__":
    unittest.main()
