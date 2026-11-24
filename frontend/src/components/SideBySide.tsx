"use client";

import { useEffect, useMemo, useState } from "react";
import {
  type DocumentSpan,
  type Finding,
  type FindingDetail,
  type SourceSpan,
  documentPdfUrl,
  getFindingDetail,
} from "@/lib/api";
import { PdfPageWithOverlays } from "./PdfPageWithOverlays";

type Props = {
  documentId: string;
  spans: DocumentSpan[];
  findings: Finding[];
};

const STATUS_COPY: Record<Finding["status"], { label: string; cls: string }> = {
  unreviewed: { label: "Hinweis – ungeprüft", cls: "text-[#9c7a1a]" },
  confirmed: { label: "Dokumentiert", cls: "text-[var(--accent)]" },
  rejected: { label: "Verworfen", cls: "text-[var(--muted)]" },
  disputed: { label: "Bestritten", cls: "text-[var(--muted)]" },
};

export function SideBySide({ documentId, spans, findings }: Props) {
  const pages = useMemo(
    () => Array.from(new Set(spans.map((s) => s.page))).sort((a, b) => a - b),
    [spans],
  );

  const findingsBySpan = useMemo(() => {
    const m = new Map<string, Finding[]>();
    for (const f of findings) {
      const list = m.get(f.document_span_id) ?? [];
      list.push(f);
      m.set(f.document_span_id, list);
    }
    return m;
  }, [findings]);

  const [activePage, setActivePage] = useState<number>(pages[0] ?? 1);
  const [activeFindingId, setActiveFindingId] = useState<string | null>(null);
  const [activeDetail, setActiveDetail] = useState<FindingDetail | null>(null);

  useEffect(() => {
    if (!activeFindingId) {
      setActiveDetail(null);
      return;
    }
    let cancelled = false;
    getFindingDetail(activeFindingId)
      .then((d) => {
        if (!cancelled) setActiveDetail(d);
      })
      .catch(() => {
        if (!cancelled) setActiveDetail(null);
      });
    return () => {
      cancelled = true;
    };
  }, [activeFindingId]);

  const highlights = useMemo(() => {
    const pageSpans = spans.filter((s) => s.page === activePage);
    return pageSpans
      .flatMap((s) => {
        const fs = findingsBySpan.get(s.id) ?? [];
        return fs
          .filter((f) => f.status === "confirmed" || f.status === "unreviewed")
          .map((f) => ({
            id: f.id,
            x0: s.bbox_x0,
            y0: s.bbox_y0,
            x1: s.bbox_x1,
            y1: s.bbox_y1,
            status:
              f.status === "confirmed"
                ? ("documented" as const)
                : ("requires_review" as const),
            active: f.id === activeFindingId,
          }));
      });
  }, [spans, findingsBySpan, activePage, activeFindingId]);

  const documentedCount = findings.filter((f) => f.status === "confirmed").length;
  const reviewCount = findings.filter((f) => f.status === "unreviewed").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 text-sm font-sans">
        <div className="flex items-center gap-2 text-[var(--muted)]">
          <span>Seite</span>
          <select
            value={activePage}
            onChange={(e) => setActivePage(Number(e.target.value))}
            className="border border-[var(--rule)] px-2 py-1 bg-transparent"
          >
            {pages.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-4 text-xs text-[var(--muted)]">
          <span>
            <span className="inline-block w-3 h-3 align-middle mr-1 bg-[rgba(122,28,28,0.22)] outline outline-1 outline-[rgb(122,28,28)]" />
            Dokumentiert · {documentedCount}
          </span>
          <span>
            <span className="inline-block w-3 h-3 align-middle mr-1 bg-[rgba(180,140,30,0.22)] outline outline-1 outline-[rgb(180,140,30)]" />
            Hinweise (nur Review) · {reviewCount}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_22rem] gap-8 items-start">
        <div className="overflow-auto border border-[var(--rule)] p-4 bg-white">
          <PdfPageWithOverlays
            pdfUrl={documentPdfUrl(documentId)}
            page={activePage}
            highlights={highlights}
            onHighlightClick={(id) =>
              setActiveFindingId((prev) => (prev === id ? null : id))
            }
          />
        </div>

        <aside className="space-y-4 sticky top-6">
          {!activeFindingId && (
            <p className="text-sm text-[var(--muted)] font-sans">
              Klicken Sie auf eine markierte Stelle, um die Belegquelle
              nebeneinander zu sehen.
            </p>
          )}
          {activeFindingId && !activeDetail && (
            <p className="text-sm text-[var(--muted)] font-sans">Lade Beleg…</p>
          )}
          {activeDetail && (
            <FindingPanel detail={activeDetail} />
          )}
        </aside>
      </div>
    </div>
  );
}

function FindingPanel({ detail }: { detail: FindingDetail }) {
  const { finding, document_span, source_spans } = detail;
  const meta = STATUS_COPY[finding.status];
  return (
    <div className="border border-[var(--rule)] p-4 space-y-4 bg-white">
      <header className="space-y-1">
        <div className={`font-sans text-xs uppercase tracking-wider ${meta.cls}`}>
          {meta.label}
        </div>
        <div className="font-sans text-xs text-[var(--muted)]">
          Detektor: {finding.detector_id} v{finding.detector_version}
        </div>
      </header>

      <section className="space-y-1">
        <h4 className="font-sans text-xs uppercase tracking-wider text-[var(--muted)]">
          Aus der Dissertation
        </h4>
        <p className="text-sm leading-relaxed">{document_span.text}</p>
        <p className="font-sans text-xs text-[var(--muted)]">
          Seite {document_span.page}
        </p>
      </section>

      <hr className="border-[var(--rule)]" />

      <section className="space-y-3">
        <h4 className="font-sans text-xs uppercase tracking-wider text-[var(--muted)]">
          Mögliche Quelle{source_spans.length === 1 ? "" : "n"}
        </h4>
        {source_spans.map((s: SourceSpan) => (
          <p key={s.id} className="text-sm leading-relaxed">
            {s.text}
          </p>
        ))}
      </section>

      {finding.status === "unreviewed" && (
        <p className="font-sans text-xs text-[var(--muted)] border-t border-[var(--rule)] pt-3">
          Diese Übereinstimmung ist ein automatisch erzeugter Hinweis und noch
          nicht redaktionell bestätigt.
        </p>
      )}
    </div>
  );
}
