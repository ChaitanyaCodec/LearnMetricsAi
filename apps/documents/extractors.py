from dataclasses import dataclass
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader
from pptx import Presentation

from .models import DocumentVersion


class DocumentExtractionError(Exception):
    pass


@dataclass(frozen=True)
class ExtractedPage:
    """
    Text extracted from one logical page/slide.

    page_number is one-based.
    For PDFs this represents the PDF page number.
    For PPTX files this represents the slide number.
    """

    page_number: int
    text: str


@dataclass(frozen=True)
class ExtractionResult:
    text: str
    page_count: int | None = None
    pages: tuple[ExtractedPage, ...] = ()


def _ensure_text(text):
    cleaned_text = text.strip()

    if not cleaned_text:
        raise DocumentExtractionError(
            "No readable text could be extracted from this file."
        )

    return cleaned_text


def _build_page_aware_text(pages):
    """
    Join page/slide text while preserving the exact character
    positions needed later for chunk-to-page mapping.
    """
    non_empty_pages = [
        page
        for page in pages
        if page.text.strip()
    ]

    if not non_empty_pages:
        raise DocumentExtractionError(
            "No readable text could be extracted from this file."
        )

    return _ensure_text(
        "\n\n".join(
            page.text.strip()
            for page in non_empty_pages
        )
    )


def _extract_pdf(file_object):
    reader = PdfReader(file_object)

    if reader.is_encrypted:
        raise DocumentExtractionError(
            "Password-protected PDF files are not supported."
        )

    pages = tuple(
        ExtractedPage(
            page_number=index + 1,
            text=page.extract_text() or "",
        )
        for index, page in enumerate(reader.pages)
    )

    return ExtractionResult(
        text=_build_page_aware_text(pages),
        page_count=len(reader.pages),
        pages=pages,
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

    pages = []

    for slide_number, slide in enumerate(
        presentation.slides,
        start=1,
    ):
        parts = []

        for shape in slide.shapes:
            if (
                getattr(shape, "has_text_frame", False)
                and shape.text.strip()
            ):
                parts.append(shape.text.strip())

        slide_text = "\n".join(parts)

        pages.append(
            ExtractedPage(
                page_number=slide_number,
                text=slide_text,
            )
        )

    pages = tuple(pages)

    return ExtractionResult(
        text=_build_page_aware_text(pages),
        page_count=len(presentation.slides),
        pages=pages,
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
    Extract document text and preserve page/slide information
    when the source format provides it.

    Database processing status is managed later by the
    processing service.
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