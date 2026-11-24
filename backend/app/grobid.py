"""GROBID client for layout-aware PDF parsing.

Calls /api/processFulltextDocument and parses TEI-XML to yield section-aware
spans. Falls back to pdfplumber via app.extraction if GROBID is unavailable
or returns no usable content.

Note: GROBID does not preserve precise page bounding boxes for paragraphs
without `teiCoordinates=p`. We pass that flag and parse `coords` attributes
to recover (page, x, y, w, h) for each paragraph.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx
from lxml import etree

from app.config import get_settings

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


@dataclass(frozen=True)
class GrobidSpan:
    page: int
    bbox: tuple[float, float, float, float]
    text: str
    section_path: list[str]


def _parse_coords(coords_attr: str) -> tuple[int, float, float, float, float] | None:
    """coords looks like 'page,x,y,w,h;page,x,y,w,h;...' for multi-line text.

    We use the first segment's page and bbox as the anchor.
    """
    if not coords_attr:
        return None
    first = coords_attr.split(";")[0]
    parts = first.split(",")
    if len(parts) < 5:
        return None
    try:
        page = int(parts[0])
        x = float(parts[1])
        y = float(parts[2])
        w = float(parts[3])
        h = float(parts[4])
    except ValueError:
        return None
    return page, x, y, x + w, y + h


def _section_path(p_element: etree._Element) -> list[str]:
    path: list[str] = []
    parent = p_element.getparent()
    while parent is not None:
        if parent.tag == f"{{{TEI_NS['tei']}}}div":
            head = parent.find("tei:head", TEI_NS)
            if head is not None and head.text:
                path.append(head.text.strip())
        parent = parent.getparent()
    return list(reversed(path))


def parse_tei(tei_xml: bytes) -> list[GrobidSpan]:
    root = etree.fromstring(tei_xml)
    spans: list[GrobidSpan] = []
    for p in root.iter(f"{{{TEI_NS['tei']}}}p"):
        coords = p.get("coords")
        parsed = _parse_coords(coords) if coords else None
        text = " ".join(p.itertext()).strip()
        if not text:
            continue
        if parsed is None:
            continue
        page, x0, y0, x1, y1 = parsed
        spans.append(
            GrobidSpan(
                page=page,
                bbox=(x0, y0, x1, y1),
                text=text,
                section_path=_section_path(p),
            )
        )
    return spans


def is_available() -> bool:
    settings = get_settings()
    if not settings.grobid_url:
        return False
    try:
        r = httpx.get(f"{settings.grobid_url}/api/isalive", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def extract_via_grobid(pdf_bytes: bytes, timeout: float = 120.0) -> list[GrobidSpan]:
    settings = get_settings()
    if not settings.grobid_url:
        raise RuntimeError("GROBID_URL not configured")
    files = {"input": ("document.pdf", pdf_bytes, "application/pdf")}
    data = {"teiCoordinates": "p", "consolidateHeader": "1"}
    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{settings.grobid_url}/api/processFulltextDocument",
            files=files,
            data=data,
        )
    response.raise_for_status()
    return parse_tei(response.content)
