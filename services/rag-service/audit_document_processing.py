#!/usr/bin/env python3
"""
Audit script to analyze document processing accuracy.
Checks for tables, images, and structured content in uploaded documents.
"""

import os
import sys
import pdfplumber
from pathlib import Path
from typing import Dict, List

def audit_pdf(pdf_path: str) -> Dict:
    """Analyze a PDF for tables, images, and content structure."""

    results = {
        "file": pdf_path,
        "pages": 0,
        "tables_found": 0,
        "images_found": 0,
        "text_chars": 0,
        "issues": [],
        "warnings": []
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            results["pages"] = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, 1):
                # Check for tables
                tables = page.extract_tables()
                if tables:
                    results["tables_found"] += len(tables)
                    for table_idx, table in enumerate(tables):
                        rows = len(table)
                        cols = len(table[0]) if table else 0
                        results["warnings"].append(
                            f"Page {page_num}: Table {table_idx + 1} "
                            f"({rows} rows × {cols} cols) will be linearized"
                        )

                # Check for images
                if page.images:
                    results["images_found"] += len(page.images)
                    results["warnings"].append(
                        f"Page {page_num}: Found {len(page.images)} image(s) "
                        f"that will be DISCARDED"
                    )

                # Check text extraction
                text = page.extract_text()
                if text:
                    results["text_chars"] += len(text)

    except Exception as e:
        results["issues"].append(f"Error reading PDF: {str(e)}")
        return results

    # Generate assessment
    if results["tables_found"] > 0:
        results["issues"].append(
            f"⚠️  {results['tables_found']} table(s) found - "
            f"structure will be LOST during processing"
        )

    if results["images_found"] > 0:
        results["issues"].append(
            f"⚠️  {results['images_found']} image(s) found - "
            f"will be COMPLETELY DISCARDED"
        )

    if not results["text_chars"]:
        results["issues"].append(
            "❌ No text extracted - PDF may be scanned image (needs OCR)"
        )

    return results

def audit_directory(directory: str) -> List[Dict]:
    """Audit all PDFs in a directory."""

    results = []
    pdf_files = list(Path(directory).rglob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return results

    print(f"Found {len(pdf_files)} PDF file(s) to audit...")
    print()

    for pdf_file in pdf_files:
        result = audit_pdf(str(pdf_file))
        results.append(result)

        # Print results
        print(f"📄 {result['file']}")
        print(f"   Pages: {result['pages']}")
        print(f"   Tables: {result['tables_found']}")
        print(f"   Images: {result['images_found']}")
        print(f"   Text chars: {result['text_chars']}")

        if result["issues"]:
            for issue in result["issues"]:
                print(f"   {issue}")

        if result["warnings"]:
            for warning in result["warnings"][:3]:  # Show first 3
                print(f"   {warning}")
            if len(result["warnings"]) > 3:
                print(f"   ... and {len(result['warnings']) - 3} more")

        print()

    # Summary
    print("=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)

    total_tables = sum(r["tables_found"] for r in results)
    total_images = sum(r["images_found"] for r in results)
    total_issues = sum(len(r["issues"]) for r in results)

    print(f"Total PDFs audited: {len(results)}")
    print(f"Total tables (will be linearized): {total_tables}")
    print(f"Total images (will be discarded): {total_images}")
    print(f"Documents with processing issues: {total_issues}")
    print()

    if total_tables > 0:
        print("⚠️  RECOMMENDATION: Enable table extraction with pdfplumber.extract_tables()")
        print("    Impact: Preserve table structure (rows, columns, cell relationships)")

    if total_images > 0:
        print("⚠️  RECOMMENDATION: Enable image processing with VisionAnalyzer")
        print("    Impact: Generate descriptions of technical diagrams and schematics")

    print()
    print("See PHASE4_STATUS.md for implementation details.")

    return results

if __name__ == "__main__":
    # Audit sample documents or user-provided path
    audit_dir = sys.argv[1] if len(sys.argv) > 1 else "data/uploads"

    if os.path.isfile(audit_dir):
        # Single file
        result = audit_pdf(audit_dir)
        print(f"Audit result: {result}")
    elif os.path.isdir(audit_dir):
        # Directory
        audit_directory(audit_dir)
    else:
        print(f"Path not found: {audit_dir}")
        print(f"Usage: python3 audit_document_processing.py [pdf_file_or_directory]")
