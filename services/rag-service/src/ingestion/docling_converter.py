"""
Docling PDF Converter

Converts a PDF file into Markdown text and extracts embedded images as PNG bytes.
Uses Docling's native export_to_markdown() for high-quality structural output
that preserves headings, tables, and list formatting.

This module has no side-effects: it does not write to disk or touch any storage.
All file I/O is handled by document_store.py.
"""

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.threaded_standard_pdf_pipeline import ThreadedStandardPdfPipeline
from docling_core.types.doc import PictureItem, TableItem

logger = logging.getLogger(__name__)

IMAGE_RESOLUTION_SCALE = 2.0


@dataclass
class DoclingResult:
    """Container for Docling conversion output."""

    markdown: str
    images: Dict[str, bytes] = field(default_factory=dict)


def _detect_device() -> AcceleratorDevice:
    try:
        import torch
        if torch.cuda.is_available():
            return AcceleratorDevice.CUDA
    except ImportError:
        pass
    return AcceleratorDevice.AUTO


def _build_converter() -> DocumentConverter:
    device = _detect_device()
    logger.info(f"Docling accelerator device: {device}")
    accelerator_options = AcceleratorOptions(device=device)

    pipeline_options = ThreadedPdfPipelineOptions(
        accelerator_options=accelerator_options,
        layout_batch_size=64,
        ocr_batch_size=4,
        table_batch_size=4,
    )
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_picture_images = True
    pipeline_options.generate_page_images = False

    return DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=ThreadedStandardPdfPipeline,
                pipeline_options=pipeline_options,
            ),
        },
    )


_converter: DocumentConverter | None = None


def _get_converter() -> DocumentConverter:
    global _converter
    if _converter is None:
        logger.info("Initializing Docling DocumentConverter")
        _converter = _build_converter()
    return _converter


def convert_pdf(pdf_path: str) -> DoclingResult:
    """
    Convert a PDF to Markdown text and extract images.

    Args:
        pdf_path: Absolute path to the PDF file on disk.

    Returns:
        DoclingResult with markdown text and a mapping of
        image filenames (e.g. "picture_1.png") to PNG bytes.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        Exception: Any Docling conversion error is propagated.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    logger.info(f"Starting Docling conversion: {path.name}")
    converter = _get_converter()
    conv_result = converter.convert(pdf_path)
    logger.info(f"Docling conversion complete: {path.name}")

    markdown = conv_result.document.export_to_markdown()

    images: Dict[str, bytes] = {}
    picture_counter = 0
    table_counter = 0

    for element, _level in conv_result.document.iterate_items():
        if isinstance(element, PictureItem):
            picture_counter += 1
            img = element.get_image(conv_result.document)
            if img is not None:
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                filename = f"picture_{picture_counter}.png"
                images[filename] = buf.getvalue()

        elif isinstance(element, TableItem):
            table_counter += 1
            img = element.get_image(conv_result.document)
            if img is not None:
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                filename = f"table_{table_counter}.png"
                images[filename] = buf.getvalue()

    logger.info(
        f"Extracted {picture_counter} picture(s) and {table_counter} table image(s) "
        f"from {path.name}"
    )

    return DoclingResult(markdown=markdown, images=images)
