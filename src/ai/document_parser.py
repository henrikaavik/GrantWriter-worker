"""Document parsing using lightweight libraries (no heavy ML dependencies)."""

from typing import Dict, Any, List
import os


class DocumentParser:
    """Parse documents using PyPDF2 and python-docx (lightweight)."""

    def parse_document(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Parse a document and extract text content.

        Args:
            file_bytes: Raw file bytes
            filename: Original filename for extension detection

        Returns:
            Dict with 'text', 'markdown', 'metadata'
        """
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            return self._parse_pdf(file_bytes, filename)
        elif ext in [".docx", ".doc"]:
            return self._parse_docx(file_bytes, filename)
        elif ext in [".xlsx", ".xls"]:
            return self._parse_xlsx(file_bytes, filename)
        elif ext == ".txt":
            return self._parse_txt(file_bytes, filename)
        else:
            return {
                "text": "",
                "markdown": "",
                "metadata": {
                    "error": "unsupported_format",
                    "message": f"Unsupported file format: {ext}"
                }
            }

    def _parse_pdf(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from PDF using PyPDF2."""
        try:
            import io
            from PyPDF2 import PdfReader

            reader = PdfReader(io.BytesIO(file_bytes))
            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

            if text and len(text.strip()) > 100:
                print(f"PDF extracted successfully: {filename}")
                return {
                    "text": text,
                    "markdown": text,
                    "metadata": {"method": "pypdf2", "pages": len(reader.pages)}
                }

            # Scanned PDF - reject it
            print(f"Scanned PDF detected, skipping: {filename}")
            return {
                "text": "",
                "markdown": "",
                "metadata": {
                    "error": "scanned_pdf",
                    "message": "This PDF appears to be scanned/image-based. Please upload a text-based PDF."
                }
            }

        except Exception as e:
            print(f"PDF extraction failed: {e}")
            return {
                "text": "",
                "markdown": "",
                "metadata": {"error": "parse_error", "message": str(e)}
            }

    def _parse_docx(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from Word document using python-docx."""
        try:
            import io
            from docx import Document

            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join(para.text for para in doc.paragraphs)

            print(f"Word doc extracted successfully: {filename}")
            return {
                "text": text,
                "markdown": text,
                "metadata": {"method": "python-docx"}
            }

        except Exception as e:
            print(f"Word doc extraction failed: {e}")
            return {
                "text": "",
                "markdown": "",
                "metadata": {"error": "parse_error", "message": str(e)}
            }

    def _parse_xlsx(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from Excel spreadsheet using openpyxl."""
        try:
            import io
            from openpyxl import load_workbook

            wb = load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
            text_parts = []

            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                text_parts.append(f"=== Sheet: {sheet_name} ===")
                for row in sheet.iter_rows(values_only=True):
                    row_text = "\t".join(str(cell) if cell is not None else "" for cell in row)
                    if row_text.strip():
                        text_parts.append(row_text)

            wb.close()
            text = "\n".join(text_parts)

            print(f"Excel extracted successfully: {filename}")
            return {
                "text": text,
                "markdown": text,
                "metadata": {"method": "openpyxl", "sheets": len(wb.sheetnames)}
            }

        except Exception as e:
            print(f"Excel extraction failed: {e}")
            return {
                "text": "",
                "markdown": "",
                "metadata": {"error": "parse_error", "message": str(e)}
            }

    def _parse_txt(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from plain text file."""
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
            print(f"Text file extracted: {filename}")
            return {
                "text": text,
                "markdown": text,
                "metadata": {"method": "plain_text"}
            }
        except Exception as e:
            print(f"Text extraction failed: {e}")
            return {
                "text": "",
                "markdown": "",
                "metadata": {"error": "parse_error", "message": str(e)}
            }


# Convenience function for simple text extraction
_parser_instance = None


def parse_document(file_bytes: bytes, filename: str) -> str:
    """
    Parse a document and return extracted text.

    Args:
        file_bytes: Raw file bytes
        filename: Original filename

    Returns:
        Extracted text content
    """
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = DocumentParser()

    result = _parser_instance.parse_document(file_bytes, filename)
    return result.get("text", "") or result.get("markdown", "")
