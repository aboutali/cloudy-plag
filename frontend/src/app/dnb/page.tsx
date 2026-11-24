"use client";

import { useState } from "react";
import { type DnbCandidate, dnbSearch } from "@/lib/api";

export default function DnbSearchPage() {
  const [name, setName] = useState("");
  const [results, setResults] = useState<DnbCandidate[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function go(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      setResults(await dnbSearch(name, 25));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler");
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-3xl tracking-tight">DNB-Suche</h1>
        <p className="font-sans text-sm text-[var(--muted)] mt-1">
          Sucht Dissertationen in der Deutschen Nationalbibliothek über die
          SRU-Schnittstelle.
        </p>
      </header>

      <form onSubmit={go} className="flex gap-2 font-sans text-sm">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Autorenname"
          className="flex-1 border border-[var(--rule)] px-2 py-1 bg-transparent"
          required
        />
        <button
          type="submit"
          disabled={loading}
          className="border border-[var(--rule)] px-4 py-1 hover:bg-[var(--rule)]/40 transition disabled:opacity-50"
        >
          {loading ? "Suche…" : "Suchen"}
        </button>
      </form>

      {error && <p className="font-sans text-xs text-[var(--accent)]">{error}</p>}

      {results && results.length === 0 && (
        <p className="font-sans text-sm text-[var(--muted)]">
          Keine Treffer.
        </p>
      )}

      {results && results.length > 0 && (
        <ul className="divide-y divide-[var(--rule)] border-t border-b border-[var(--rule)]">
          {results.map((c, i) => (
            <li key={c.record_id ?? i} className="py-3 space-y-1">
              <div className="flex items-baseline justify-between gap-6">
                <h3>{c.title}</h3>
                <span className="font-sans text-xs text-[var(--muted)] tabular-nums">
                  {c.year ?? "—"}
                </span>
              </div>
              {c.authors.length > 0 && (
                <div className="font-sans text-xs text-[var(--muted)]">
                  {c.authors.join("; ")}
                </div>
              )}
              {c.institution && (
                <div className="font-sans text-xs text-[var(--muted)]">
                  {c.institution}
                </div>
              )}
              {c.resolver_url && (
                <div className="font-sans text-xs">
                  <a
                    href={c.resolver_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[var(--accent)] underline break-all"
                  >
                    {c.resolver_url}
                  </a>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
