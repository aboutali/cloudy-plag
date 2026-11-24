import { API_BASE_URL, listAuditEvents } from "@/lib/api";

export const dynamic = "force-dynamic";

const ACTION_LABELS: Record<string, string> = {
  "document.ingested": "Dokument eingelesen",
  "document.linked_to_person": "Person verknüpft",
  "person.created": "Person angelegt",
  "person.updated": "Person aktualisiert",
  "source.ingested": "Quelle eingelesen",
  "finding.reviewed": "Fundstelle begutachtet",
  "detector.ngram.run": "n-Gram-Detektor",
  "detector.paraphrase.run": "Paraphrasen-Detektor",
};

const KNOWN_ENTITY_TYPES = [
  "document",
  "person",
  "source",
  "finding",
] as const;

export default async function AuditPage({
  searchParams,
}: {
  searchParams: Promise<{ entity_type?: string; entity_id?: string; limit?: string }>;
}) {
  const sp = await searchParams;
  const limit = sp.limit ? Math.min(Number(sp.limit), 1000) : 200;
  const events = await listAuditEvents({
    entity_type: sp.entity_type,
    entity_id: sp.entity_id,
    limit,
  }).catch(() => []);

  const downloadUrl = (() => {
    const u = new URL(`${API_BASE_URL}/audit/events.jsonl`);
    if (sp.entity_type) u.searchParams.set("entity_type", sp.entity_type);
    if (sp.entity_id) u.searchParams.set("entity_id", sp.entity_id);
    u.searchParams.set("limit", String(limit));
    return u.toString();
  })();

  return (
    <section className="space-y-6">
      <header className="flex items-end justify-between gap-6 flex-wrap">
        <div>
          <h1 className="text-3xl tracking-tight">Audit-Log</h1>
          <p className="font-sans text-sm text-[var(--muted)] mt-1">
            Append-only. Datenbank-Trigger blockiert UPDATE und DELETE.
          </p>
        </div>
        <a
          href={downloadUrl}
          className="font-sans text-sm border border-[var(--rule)] px-3 py-1 hover:bg-[var(--rule)]/40 transition"
        >
          ↓ JSONL herunterladen
        </a>
      </header>

      <form
        action="/audit"
        className="flex flex-wrap gap-2 font-sans text-sm items-end"
      >
        <label className="space-y-1">
          <span className="text-[var(--muted)] block">Entitätstyp</span>
          <select
            name="entity_type"
            defaultValue={sp.entity_type ?? ""}
            className="border border-[var(--rule)] px-2 py-1 bg-transparent"
          >
            <option value="">— alle —</option>
            {KNOWN_ENTITY_TYPES.map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-1 flex-1 min-w-[20rem]">
          <span className="text-[var(--muted)] block">Entitäts-ID</span>
          <input
            name="entity_id"
            defaultValue={sp.entity_id ?? ""}
            placeholder="UUID"
            className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
          />
        </label>
        <label className="space-y-1">
          <span className="text-[var(--muted)] block">Limit</span>
          <input
            name="limit"
            type="number"
            defaultValue={sp.limit ?? "200"}
            min={1}
            max={1000}
            className="w-24 border border-[var(--rule)] px-2 py-1 bg-transparent"
          />
        </label>
        <button
          type="submit"
          className="border border-[var(--rule)] px-3 py-1 hover:bg-[var(--rule)]/40 transition"
        >
          Filtern
        </button>
        {(sp.entity_type || sp.entity_id) && (
          <a
            href="/audit"
            className="text-[var(--muted)] underline"
          >
            zurücksetzen
          </a>
        )}
      </form>

      <p className="font-sans text-xs text-[var(--muted)]">
        {events.length} Ereignis{events.length === 1 ? "" : "se"}.
      </p>

      <div className="overflow-x-auto border border-[var(--rule)]">
        <table className="w-full text-xs font-sans">
          <thead>
            <tr className="bg-[var(--rule)]/30 text-left">
              <th className="px-3 py-2">Zeit</th>
              <th className="px-3 py-2">Akteur</th>
              <th className="px-3 py-2">Aktion</th>
              <th className="px-3 py-2">Entität</th>
              <th className="px-3 py-2">Payload</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--rule)]">
            {events.map((e) => (
              <tr key={e.id}>
                <td className="px-3 py-2 align-top tabular-nums whitespace-nowrap">
                  {new Date(e.occurred_at).toLocaleString("de-DE")}
                </td>
                <td className="px-3 py-2 align-top">{e.actor}</td>
                <td className="px-3 py-2 align-top">
                  {ACTION_LABELS[e.action] ?? e.action}
                </td>
                <td className="px-3 py-2 align-top">
                  {e.entity_type}
                  {e.entity_id && (
                    <div className="text-[var(--muted)] truncate max-w-[12rem]">
                      {e.entity_id}
                    </div>
                  )}
                </td>
                <td className="px-3 py-2 align-top text-[var(--muted)]">
                  <code className="text-[10px] break-all">
                    {JSON.stringify(e.payload)}
                  </code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
