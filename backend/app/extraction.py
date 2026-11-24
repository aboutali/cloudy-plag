from __future__ import annotations

import io
from dataclasses import dataclass

import pdfplumber


@dataclass(frozen=True)
class ExtractedSpan:
    page: int
    bbox: tuple[float, float, float, float]
    text: str


def extract_spans(pdf_bytes: bytes) -> list[ExtractedSpan]:
    """Extract paragraph-ish spans from a PDF, preserving (page, bbox).

    First-cut implementation using pdfplumber word grouping. Replace with
    GROBID for proper layout/section awareness in a later phase.
    """
    spans: list[ExtractedSpan] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            words = page.extract_words(use_text_flow=True, keep_blank_chars=False)
            if not words:
                continue
            spans.extend(_group_words_to_spans(words, page_index))
    return spans


def _group_words_to_spans(words: list[dict], page_index: int) -> list[ExtractedSpan]:
    """Group consecutive words into line/paragraph-level spans.

    Heuristic: words on roughly the same y-baseline form a line; lines
    separated by a blank-line-sized gap form a paragraph span.
    """
    if not words:
        return []

    lines: list[list[dict]] = []
    current: list[dict] = []
    last_top: float | None = None
    line_tol = 2.5

    for w in sorted(words, key=lambda w: (round(w["top"], 1), w["x0"])):
        if last_top is None or abs(w["top"] - last_top) <= line_tol:
            current.append(w)
            last_top = w["top"] if last_top is None else last_top
        else:
            lines.append(current)
            current = [w]
            last_top = w["top"]
    if current:
        lines.append(current)

    spans: list[ExtractedSpan] = []
    paragraph: list[dict] = []
    prev_bottom: float | None = None
    paragraph_gap = 6.0

    def flush() -> None:
        if not paragraph:
            return
        x0 = min(w["x0"] for w in paragraph)
        y0 = min(w["top"] for w in paragraph)
        x1 = max(w["x1"] for w in paragraph)
        y1 = max(w["bottom"] for w in paragraph)
        text = " ".join(w["text"] for w in paragraph).strip()
        if text:
            spans.append(
                ExtractedSpan(
                    page=page_index,
                    bbox=(x0, y0, x1, y1),
                    text=text,
                )
            )

    for line in lines:
        line_top = min(w["top"] for w in line)
        if prev_bottom is not None and (line_top - prev_bottom) > paragraph_gap:
            flush()
            paragraph = []
        paragraph.extend(line)
        prev_bottom = max(w["bottom"] for w in line)
    flush()

    return spans
