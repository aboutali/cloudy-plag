from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[\.!?])\s+(?=[A-ZÄÖÜ])")


def segment_into_spans(text: str, max_chars: int = 600) -> list[str]:
    """Cheap segmenter for plain-text sources.

    Splits on sentence boundaries, then packs sentences into spans up to
    `max_chars`. Keeps each span coherent enough for paragraph-grain matches.
    """
    text = text.replace("\r\n", "\n")
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    spans: list[str] = []
    for paragraph in paragraphs:
        sentences = _SENTENCE_SPLIT.split(paragraph)
        buffer: list[str] = []
        length = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if length + len(sentence) + 1 > max_chars and buffer:
                spans.append(" ".join(buffer))
                buffer = []
                length = 0
            buffer.append(sentence)
            length += len(sentence) + 1
        if buffer:
            spans.append(" ".join(buffer))
    return spans
