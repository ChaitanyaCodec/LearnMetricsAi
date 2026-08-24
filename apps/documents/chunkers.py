from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class ChunkData:
    chunk_index: int
    content: str
    character_start: int
    character_end: int


def chunk_text(
    text,
    *,
    chunk_size=None,
    chunk_overlap=None,
):
    """
    Split extracted text into overlapping, readable chunks.

    Prefers paragraph or word boundaries near the chunk limit.
    """
    chunk_size = (
        chunk_size
        or settings.DOCUMENTS_CHUNK_SIZE
    )

    chunk_overlap = (
        chunk_overlap
        if chunk_overlap is not None
        else settings.DOCUMENTS_CHUNK_OVERLAP
    )

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be zero or greater and smaller "
            "than chunk_size."
        )

    text = text.strip()

    if not text:
        return []

    chunks = []
    text_length = len(text)
    start = 0
    chunk_index = 0

    while start < text_length:
        maximum_end = min(
            start + chunk_size,
            text_length,
        )

        end = maximum_end

        if maximum_end < text_length:
            minimum_preferred_end = start + (
                chunk_size // 2
            )

            paragraph_end = text.rfind(
                "\n",
                minimum_preferred_end,
                maximum_end,
            )

            word_end = text.rfind(
                " ",
                minimum_preferred_end,
                maximum_end,
            )

            end = max(paragraph_end, word_end)

            if end <= start:
                end = maximum_end

        content = text[start:end].strip()

        if content:
            chunks.append(
                ChunkData(
                    chunk_index=chunk_index,
                    content=content,
                    character_start=start,
                    character_end=end,
                )
            )
            chunk_index += 1

        if end >= text_length:
            break

        start = max(
            end - chunk_overlap,
            start + 1,
        )

    return chunks