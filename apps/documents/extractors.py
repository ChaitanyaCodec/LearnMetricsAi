from dataclasses import dataclass
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader
from pptx import Presentation

from .models import DocumentVersion


class DocumentExtractionError(Exception):
    pass


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    page_count: int | None = None


def _ensure_text(text):
    cleaned_text = text.strip()

    if not cleaned_text:
        raise DocumentExtractionError(
            "No readable text could be extracted from this file."
        )

    return cleaned_text


def _extract_pdf(file_object):
    reader = PdfReader(file_object)

    if reader.is_encrypted:
        raise DocumentExtractionError(
            "Password-protected PDF files are not supported."
        )

    page_texts = []

    for page in reader.pages:
        page_texts.append(page.extract_text() or "")

    return ExtractionResult(
        text=_ensure_text("\n\n".join(page_texts)),
        page_count=len(reader.pages),
    )


def _extract_docx(file_object):
    document = DocxDocument(file_object)

    parts = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    for table in document.tables:
        for row in table.rows:
            row_text = " | ".join(
                cell.text.strip()
                for cell in row.cells
                if cell.text.strip()
            )

            if row_text:
                parts.append(row_text)

    return ExtractionResult(
        text=_ensure_text("\n\n".join(parts)),
    )


def _extract_pptx(file_object):
    presentation = Presentation(file_object)
    slide_texts = []

    for slide in presentation.slides:
        parts = []

        for shape in slide.shapes:
            if (
                getattr(shape, "has_text_frame", False)
                and shape.text.strip()
            ):
                parts.append(shape.text.strip())

        if parts:
            slide_texts.append("\n".join(parts))

    return ExtractionResult(
        text=_ensure_text("\n\n".join(slide_texts)),
        page_count=len(presentation.slides),
    )


def _extract_txt(file_object):
    raw_content = file_object.read()

    try:
        text = raw_content.decode("utf-8")
    except UnicodeDecodeError:
        text = raw_content.decode("latin-1")

    return ExtractionResult(
        text=_ensure_text(text),
    )


def extract_document_version(document_version: DocumentVersion):
    """
    Extract text only. Database processing status is managed later
    by the processing service.
    """
    extension = Path(
        document_version.original_filename
    ).suffix.lower()

    try:
        with document_version.source_file.open("rb") as file_object:
            if extension == ".pdf":
                return _extract_pdf(file_object)

            if extension == ".docx":
                return _extract_docx(file_object)

            if extension == ".pptx":
                return _extract_pptx(file_object)

            if extension == ".txt":
                return _extract_txt(file_object)

    except DocumentExtractionError:
        raise
    except Exception as exc:
        raise DocumentExtractionError(
            f"Unable to extract document text: {exc}"
        ) from exc

    raise DocumentExtractionError(
        f"Unsupported file type: {extension}."
    )