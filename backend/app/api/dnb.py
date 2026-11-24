from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.dnb import DnbCandidate, search_dissertations

router = APIRouter(prefix="/dnb", tags=["dnb"])


class DnbCandidateOut(BaseModel):
    title: str
    authors: list[str]
    year: str | None = None
    institution: str | None = None
    urn: str | None = None
    resolver_url: str | None = None
    record_id: str | None = None

    @classmethod
    def from_dataclass(cls, c: DnbCandidate) -> "DnbCandidateOut":
        return cls(
            title=c.title,
            authors=c.authors,
            year=c.year,
            institution=c.institution,
            urn=c.urn,
            resolver_url=c.resolver_url,
            record_id=c.record_id,
        )


@router.get("/search", response_model=list[DnbCandidateOut])
async def dnb_search(
    name: str = Query(..., description="Author name (full or partial)"),
    limit: int = Query(10, ge=1, le=50),
) -> list[DnbCandidateOut]:
    try:
        candidates = await search_dissertations(name, max_records=limit)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"DNB error: {e}") from e
    return [DnbCandidateOut.from_dataclass(c) for c in candidates]
