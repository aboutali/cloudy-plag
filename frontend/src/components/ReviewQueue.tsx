"use client";

import { useEffect, useState } from "react";
import {
  API_BASE_URL,
  type Finding,
  type FindingDetail,
  getFindingDetail,
} from "@/lib/api";

const DECISION_LABELS: Record<string, string> = {
  confirm: "Bestätigen",
  reject: "Verwerfen",
  dispute: "Bestreiten",
  request_more_evidence: "Mehr Belege anfordern",
};

export function ReviewQueue({ findings }: { findings: Finding[] }) {
  const [items, setItems] = useState<Finding[]>(findings);
  const [reviewerHandle, setReviewerHandle] = useState<string>("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      setReviewerHandle(window.localStorage.getItem("cloudy:handle") ?? "");
    }
  }, []);

  function persistHandle(h: string) {
    setReviewerHandle(h);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("cloudy:handle", h);
    }
  }

  async function submit(findingId: string, decision: string) {
    if (!reviewerHandle) {
      alert("Bitte zunächst ein Reviewer-Handle eintragen.");
      return;
    }
    const res = await fetch(`${API_BASE_URL}/findings/${findingId}/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reviewer_handle: reviewerHandle, decision }),
    });
    if (!res.ok) {
      alert(`Fehler: HTTP ${res.status}`);
      return;
    }
    setItems((prev) => prev.filter((f) => f.id !== findingId));
  }

  return (
    <div className="space-y-6">
      <label className="block text-sm font-sans">
        <span className="text-[var(--muted)]">Reviewer-Handle</span>
        <input
          value={reviewerHandle}
          onChange={(e) => persistHandle(e.target.value)}
          placeholder="z. B. ariadne"
          className="mt-1 block w-64 border border-[var(--rule)] px-2 py-1 bg-transparent"
        />
      </label>

      {items.length === 0 && (
        <p className="font-sans text-sm text-[var(--muted)]">
          Keine offenen Hinweise.
        </p>
      )}

      <ul className="space-y-4">
        {items.map((f) => (
          <FindingCard
            key={f.id}
            finding={f}
            onDecision={(d) => submit(f.id, d)}
          />
        ))}
      </ul>
    </div>
  );
}

function FindingCard({
  finding,
  onDecision,
}: {
  finding: Finding;
  onDecision: (d: string) => void;
}) {
  const [detail, setDetail] = useState<FindingDetail | null>(null);
  useEffect(() => {
    getFindingDetail(finding.id).then(setDetail).catch(() => setDetail(null));
  }, [finding.id]);

  return (
    <li className="border border-[var(--rule)] p-4 space-y-3 bg-white">
      <div className="font-sans text-xs text-[var(--muted)]">
        {finding.detector_id} v{finding.detector_version} · {finding.kind}
      </div>
      {detail ? (
        <>
          <div>
            <div className="font-sans text-xs uppercase tracking-wider text-[var(--muted)] mb-1">
              Aus der Dissertation · Seite {detail.document_span.page}
            </div>
            <p className="text-sm leading-relaxed">{detail.document_span.text}</p>
          </div>
          <div>
            <div className="font-sans text-xs uppercase tracking-wider text-[var(--muted)] mb-1">
              Mögliche Quelle
            </div>
            {detail.source_spans.map((s) => (
              <p key={s.id} className="text-sm leading-relaxed">
                {s.text}
              </p>
            ))}
          </div>
        </>
      ) : (
        <p className="font-sans text-xs text-[var(--muted)]">Lade Beleg…</p>
      )}
      <div className="flex flex-wrap gap-2 pt-2 font-sans text-sm">
        {Object.entries(DECISION_LABELS).map(([d, label]) => (
          <button
            key={d}
            type="button"
            onClick={() => onDecision(d)}
            className="border border-[var(--rule)] px-3 py-1 hover:bg-[var(--rule)]/40 transition"
          >
            {label}
          </button>
        ))}
      </div>
    </li>
  );
}
