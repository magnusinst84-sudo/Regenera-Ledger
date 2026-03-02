"""
data/parsers/pdf_extractor.py
Teammate 2 — Data / Matching

Extracts clean text from ESG report PDFs and supplier documents.
Output: clean text string passed to backend T1 Gemini routes.
"""

from __future__ import annotations

import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Union

from pdfminer.high_level import extract_text, extract_text_to_fp
from pdfminer.layout import LAParams

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def extract_text_from_pdf(source: Union[str, Path, bytes, BytesIO]) -> str:
    """
    Extract and clean text from a PDF.

    Args:
        source: File path (str / Path), raw bytes, or BytesIO object.

    Returns:
        A single cleaned text string suitable for Gemini prompting.

    Raises:
        ValueError: If the source type is unsupported.
        RuntimeError: If text extraction fails.
    """
    try:
        raw = _load_source(source)
        text = _extract(raw)
        return _clean(text)
    except Exception as exc:
        logger.error("PDF extraction failed: %s", exc)
        raise RuntimeError(f"PDF extraction failed: {exc}") from exc


def extract_pages_from_pdf(source: Union[str, Path, bytes, BytesIO]) -> list[str]:
    """
    Extract text page-by-page from a PDF.

    Returns:
        List of cleaned strings, one per page.
    """
    try:
        raw = _load_source(source)
        from pdfminer.high_level import extract_pages as _extract_pages
        from pdfminer.layout import LTTextContainer

        pages: list[str] = []
        for page_layout in _extract_pages(raw):
            page_text = ""
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    page_text += element.get_text()
            pages.append(_clean(page_text))
        return pages
    except Exception as exc:
        logger.error("PDF page extraction failed: %s", exc)
        raise RuntimeError(f"PDF page extraction failed: {exc}") from exc


# ──────────────────────────────────────────────
# Internals
# ──────────────────────────────────────────────

def _load_source(source: Union[str, Path, bytes, BytesIO]) -> BytesIO:
    """Normalise the various input types to a BytesIO stream."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        return BytesIO(path.read_bytes())
    elif isinstance(source, bytes):
        return BytesIO(source)
    elif isinstance(source, BytesIO):
        source.seek(0)
        return source
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")


def _extract(stream: BytesIO) -> str:
    """Run pdfminer extraction with tuned LAParams."""
    laparams = LAParams(
        line_margin=0.5,
        word_margin=0.1,
        char_margin=2.0,
        all_texts=True,
    )
    stream.seek(0)
    return extract_text(stream, laparams=laparams)


def _clean(text: str) -> str:
    """
    Clean extracted text:
    - Collapse excessive whitespace / blank lines
    - Remove page-number-only lines
    - Strip control characters
    """
    if not text:
        return ""

    # Remove control chars except newline / tab
    text = re.sub(r"[^\S\n\t ]+", " ", text)

    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    # Drop lines that are just page numbers or dashes
    lines = text.splitlines()
    clean_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        # Skip page-number-only lines and pure-dash separators
        if re.fullmatch(r"[\d\s\-–—]*", stripped):
            continue
        clean_lines.append(line)

    # Collapse 3+ consecutive blank lines to 2
    result = "\n".join(clean_lines)
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()


# ──────────────────────────────────────────────
# CLI helper (quick test)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pdf_extractor.py <path_to_pdf>")
        sys.exit(1)

    extracted = extract_text_from_pdf(sys.argv[1])
    print(f"[Extracted {len(extracted)} characters]\n")
    print(extracted[:3000])
