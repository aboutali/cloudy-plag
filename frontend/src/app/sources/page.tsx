import Link from "next/link";
import { listSources } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function SourcesPage() {
  const sources = await listSources().catch(() => []);
  return (
    <section className="space-y-8">
      <header className="flex items-end justify-between gap-6">
        <div>
          <h1 className="text-3xl tracking-tight">Quellen</h1>
          <p className="font-sans text-sm text-[var(--muted)] mt-1">
            Vergleichskorpus für Übernahme-Detektoren.
          </p>
        </div>
        <Link
          href="/sources/new"
          className="font-sans text-sm border border-[var(--rule)] px-3 py-1 hover:bg-[var(--rule)]/40 transition"
        >
          + Quelle hinzufügen
        </Link>
      </header>

      {sources.length === 0 && (
        <p className="font-sans text-sm text-[var(--muted)]">
          Noch keine Quellen hinterlegt.
        </p>
      )}

      <ul className="divide-y divide-[var(--rule)] border-t border-b border-[var(--rule)]">
        {sources.map((s) => (
          <li key={s.id} className="py-3">
            <div className="flex items-baseline justify-between gap-6">
              <div>
                <div>{s.title}</div>
                {s.authors && s.authors.length > 0 && (
                  <div className="font-sans text-xs text-[var(--muted)]">
                    {s.authors.join(", ")}
                  </div>
                )}
              </div>
              <span className="font-sans text-xs text-[var(--muted)] tabular-nums">
                {s.kind} · {s.year ?? "—"}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
