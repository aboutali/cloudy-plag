"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ingestSourceText, ingestSourceUrl } from "@/lib/api";

const KINDS = [
  { v: "paper", l: "Wissenschaftlicher Aufsatz" },
  { v: "book", l: "Buch" },
  { v: "webpage", l: "Webseite" },
  { v: "dissertation", l: "Andere Dissertation" },
  { v: "other", l: "Sonstige" },
];

type Mode = "text" | "url";

export default function NewSourcePage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("text");

  const [kind, setKind] = useState("paper");
  const [title, setTitle] = useState("");
  const [authors, setAuthors] = useState("");
  const [year, setYear] = useState("");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (mode === "text") {
        await ingestSourceText({
          kind,
          title,
          text,
          authors: authors
            ? authors.split(",").map((a) => a.trim()).filter(Boolean)
            : undefined,
          year: year ? Number(year) : undefined,
        });
      } else {
        await ingestSourceUrl({
          url,
          kind,
          title: title || undefined,
          authors: authors
            ? authors.split(",").map((a) => a.trim()).filter(Boolean)
            : undefined,
          year: year ? Number(year) : undefined,
        });
      }
      router.push("/sources");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-6 max-w-2xl">
      <header>
        <h1 className="text-3xl tracking-tight">Quelle hinzufügen</h1>
        <p className="font-sans text-sm text-[var(--muted)] mt-1">
          Bitte Zitatrecht (§ 51 UrhG) beachten — nur das für die Prüfung
          Notwendige speichern.
        </p>
      </header>

      <div className="flex gap-2 border-b border-[var(--rule)] font-sans text-sm">
        {(["text", "url"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={`px-3 py-1 border-b-2 -mb-px ${
              mode === m
                ? "border-[var(--accent)] text-[var(--accent)]"
                : "border-transparent text-[var(--muted)]"
            }`}
          >
            {m === "text" ? "Text einfügen" : "Aus URL"}
          </button>
        ))}
      </div>

      <form onSubmit={submit} className="space-y-4 font-sans text-sm">
        <div className="grid grid-cols-2 gap-3">
          <label className="block space-y-1">
            <span className="text-[var(--muted)]">Art</span>
            <select
              value={kind}
              onChange={(e) => setKind(e.target.value)}
              className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
            >
              {KINDS.map((k) => (
                <option key={k.v} value={k.v}>
                  {k.l}
                </option>
              ))}
            </select>
          </label>
          <label className="block space-y-1">
            <span className="text-[var(--muted)]">Jahr</span>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
            />
          </label>
        </div>

        <label className="block space-y-1">
          <span className="text-[var(--muted)]">
            Titel {mode === "url" && "(optional, sonst aus Seite)"}
          </span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required={mode === "text"}
            className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
          />
        </label>
        <label className="block space-y-1">
          <span className="text-[var(--muted)]">
            Autor:innen (kommagetrennt)
          </span>
          <input
            value={authors}
            onChange={(e) => setAuthors(e.target.value)}
            className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
          />
        </label>

        {mode === "text" ? (
          <label className="block space-y-1">
            <span className="text-[var(--muted)]">Text</span>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              required
              rows={14}
              className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent font-serif"
            />
          </label>
        ) : (
          <label className="block space-y-1">
            <span className="text-[var(--muted)]">URL</span>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
            />
          </label>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="border border-[var(--rule)] px-4 py-1 hover:bg-[var(--rule)]/40 transition disabled:opacity-50"
        >
          {submitting ? "Speichere…" : "Speichern"}
        </button>
        {error && <p className="text-[var(--accent)]">{error}</p>}
      </form>
    </section>
  );
}
