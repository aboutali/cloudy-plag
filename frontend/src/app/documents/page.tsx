import Link from "next/link";
import { listDocuments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DocumentsPage() {
  let documents: Awaited<ReturnType<typeof listDocuments>> = [];
  let error: string | null = null;
  try {
    documents = await listDocuments();
  } catch (e) {
    error = e instanceof Error ? e.message : "Unbekannter Fehler";
  }

  return (
    <section className="space-y-8">
      <header className="flex items-end justify-between gap-6">
        <div className="space-y-2">
          <h1 className="text-3xl tracking-tight">Dokumente</h1>
          <p className="text-sm text-[var(--muted)] font-sans">
            Eingelesene Dissertationen. Findings erscheinen hier erst nach
            redaktioneller Bestätigung.
          </p>
        </div>
        <Link
          href="/documents/new"
          className="font-sans text-sm border border-[var(--rule)] px-3 py-1 hover:bg-[var(--rule)]/40 transition"
        >
          + Dissertation einlesen
        </Link>
      </header>

      {error && (
        <p className="font-sans text-sm text-[var(--accent)]">
          API nicht erreichbar: {error}
        </p>
      )}

      {!error && documents.length === 0 && (
        <p className="font-sans text-sm text-[var(--muted)]">
          Noch keine Dokumente eingelesen.
        </p>
      )}

      <ul className="divide-y divide-[var(--rule)] border-t border-b border-[var(--rule)]">
        {documents.map((d) => (
          <li key={d.id} className="py-4">
            <Link
              href={`/documents/${d.id}`}
              className="block hover:bg-[var(--rule)]/30 -mx-4 px-4 py-2 transition"
            >
              <div className="flex items-baseline justify-between gap-6">
                <h2 className="text-lg">{d.title}</h2>
                <span className="font-sans text-xs text-[var(--muted)] tabular-nums shrink-0">
                  {d.year ?? "—"}
                </span>
              </div>
              <div className="font-sans text-xs text-[var(--muted)] mt-1">
                {[d.institution, d.degree].filter(Boolean).join(" · ") || "—"}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
