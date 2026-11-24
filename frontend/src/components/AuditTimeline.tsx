import { type AuditEvent, listAuditEvents } from "@/lib/api";

const ACTION_LABELS: Record<string, string> = {
  "document.ingested": "Dokument eingelesen",
  "document.linked_to_person": "Person verknüpft",
  "person.created": "Person angelegt",
  "person.updated": "Person aktualisiert",
  "source.ingested": "Quelle eingelesen",
  "finding.reviewed": "Fundstelle begutachtet",
  "detector.ngram.run": "n-Gram-Detektor ausgeführt",
  "detector.paraphrase.run": "Paraphrasen-Detektor ausgeführt",
};

function summarize(e: AuditEvent): string {
  const p = e.payload as Record<string, string | number | boolean | null>;
  switch (e.action) {
    case "finding.reviewed":
      return `${p.decision} → ${p.new_status}`;
    case "detector.ngram.run":
    case "detector.paraphrase.run":
      return `${p.findings_created} Hinweise`;
    case "source.ingested":
      return `${p.kind} · ${p.span_count} Spans`;
    case "document.ingested":
      return `${p.span_count} Spans · Extraktor ${p.extractor ?? "—"}`;
    default:
      return "";
  }
}

export async function AuditTimeline({
  entityType,
  entityId,
  limit = 50,
}: {
  entityType: string;
  entityId: string;
  limit?: number;
}) {
  const events = await listAuditEvents({
    entity_type: entityType,
    entity_id: entityId,
    limit,
  }).catch(() => [] as AuditEvent[]);

  if (events.length === 0) {
    return (
      <p className="font-sans text-xs text-[var(--muted)]">
        Keine Ereignisse.
      </p>
    );
  }

  return (
    <ol className="space-y-2 font-sans text-xs">
      {events.map((e) => (
        <li
          key={e.id}
          className="flex gap-3 border-l-2 border-[var(--rule)] pl-3"
        >
          <span className="text-[var(--muted)] tabular-nums whitespace-nowrap">
            {new Date(e.occurred_at).toLocaleString("de-DE")}
          </span>
          <span>
            {ACTION_LABELS[e.action] ?? e.action}{" "}
            <span className="text-[var(--muted)]">{summarize(e)}</span>
          </span>
          <span className="text-[var(--muted)] ml-auto">{e.actor}</span>
        </li>
      ))}
    </ol>
  );
}
