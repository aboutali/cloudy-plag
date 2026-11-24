"""Deutsche Nationalbibliothek (DNB) search via SRU.

Endpoint: https://services.dnb.de/sru/dnb
Query language: CQL.

Returns dissertation candidates parsed from MARC21-XML records. Each result
includes title, authors, year, institution if available, and a best-effort
PDF resolver URL (URN/DOI). Caller is responsible for checking license and
fetching the PDF separately.

Reference: https://www.dnb.de/EN/Professionell/Metadatendienste/Datenbezug/SRU/sru.html
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx
from lxml import etree

SRU_ENDPOINT = "https://services.dnb.de/sru/dnb"

NS = {
    "srw": "http://www.loc.gov/zing/srw/",
    "marc": "http://www.loc.gov/MARC21/slim",
}


@dataclass(frozen=True)
class DnbCandidate:
    title: str
    authors: list[str]
    year: str | None
    institution: str | None
    urn: str | None
    resolver_url: str | None
    record_id: str | None


def _text(record: etree._Element, xpath: str) -> str | None:
    el = record.xpath(xpath, namespaces=NS)
    if not el:
        return None
    return el[0].text.strip() if el[0].text else None


def _all_text(record: etree._Element, xpath: str) -> list[str]:
    return [el.text.strip() for el in record.xpath(xpath, namespaces=NS) if el.text]


def _build_query(name: str) -> str:
    # WOE = "Werk Online Erscheinungsform". mat=dis filters to dissertations.
    # Quote the name to keep it together as a phrase.
    safe = name.replace('"', "")
    return f'WOE="{safe}" and mat=diss'


async def search_dissertations(name: str, max_records: int = 10) -> list[DnbCandidate]:
    params = {
        "version": "1.1",
        "operation": "searchRetrieve",
        "query": _build_query(name),
        "recordSchema": "MARC21-xml",
        "maximumRecords": str(max_records),
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(SRU_ENDPOINT, params=params)
    response.raise_for_status()

    root = etree.fromstring(response.content)
    records = root.xpath(".//marc:record", namespaces=NS)
    candidates: list[DnbCandidate] = []
    for record in records:
        title = _text(record, './/marc:datafield[@tag="245"]/marc:subfield[@code="a"]')
        if not title:
            continue
        # Authors: 100 (main), 700 (additional)
        authors = _all_text(
            record,
            './/marc:datafield[@tag="100"]/marc:subfield[@code="a"]',
        ) + _all_text(
            record,
            './/marc:datafield[@tag="700"]/marc:subfield[@code="a"]',
        )
        year = _text(record, './/marc:datafield[@tag="264"]/marc:subfield[@code="c"]')
        institution = _text(record, './/marc:datafield[@tag="502"]/marc:subfield[@code="b"]')
        urn = _text(record, './/marc:datafield[@tag="024"]/marc:subfield[@code="a"]')
        record_id = _text(record, './/marc:controlfield[@tag="001"]')
        resolver_url = (
            f"https://nbn-resolving.org/{urn}" if urn and urn.startswith("urn:") else None
        )
        candidates.append(
            DnbCandidate(
                title=title,
                authors=authors,
                year=year,
                institution=institution,
                urn=urn,
                resolver_url=resolver_url,
                record_id=record_id,
            )
        )
    return candidates
