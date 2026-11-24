from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup
from readability import Document as ReadabilityDocument


@dataclass(frozen=True)
class ExtractedHtml:
    title: str
    text: str


def extract_main_text(html: str) -> ExtractedHtml:
    """Reduce a webpage to its main article text and a title.

    Uses readability-lxml to drop navigation/boilerplate, then strips remaining
    tags. The result feeds into the same span segmenter as the manual paste path.
    """
    rd = ReadabilityDocument(html)
    title = rd.short_title() or rd.title() or ""
    summary_html = rd.summary(html_partial=True)
    soup = BeautifulSoup(summary_html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all(["p", "li"])]
    paragraphs = [p for p in paragraphs if p]
    text = "\n\n".join(paragraphs) or soup.get_text("\n", strip=True)
    return ExtractedHtml(title=title.strip(), text=text)
