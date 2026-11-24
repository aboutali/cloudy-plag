"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  type Person,
  ingestDocumentFile,
  listPersons,
} from "@/lib/api";

export default function NewDocumentPage() {
  const router = useRouter();
  const [persons, setPersons] = useState<Person[]>([]);
  const [title, setTitle] = useState("");
  const [year, setYear] = useState("");
  const [institution, setInstitution] = useState("");
  const [degree, setDegree] = useState("");
  const [personId, setPersonId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listPersons().then(setPersons).catch(() => setPersons([]));
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Bitte eine PDF-Datei auswählen.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const form = new FormData();
      form.set("file", file);
      form.set("title", title);
      if (year) form.set("year", year);
      if (institution) form.set("institution", institution);
      if (degree) form.set("degree", degree);
      if (personId) form.set("person_id", personId);
      const { document } = await ingestDocumentFile(form);
      router.push(`/documents/${document.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-6 max-w-xl">
      <header>
        <h1 className="text-3xl tracking-tight">Dissertation einlesen</h1>
        <p className="font-sans text-sm text-[var(--muted)] mt-1">
          PDF wird unveränderlich gespeichert. Hash und Provenienz werden
          protokolliert.
        </p>
      </header>
      <form onSubmit={submit} className="space-y-4 font-sans text-sm">
        <label className="block space-y-1">
          <span className="text-[var(--muted)]">PDF-Datei</span>
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
            className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
          />
        </label>
        <label className="block space-y-1">
          <span className="text-[var(--muted)]">Titel</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
          />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block space-y-1">
            <span className="text-[var(--muted)]">Jahr</span>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
            />
          </label>
          <label className="block space-y-1">
            <span className="text-[var(--muted)]">Grad</span>
            <input
              value={degree}
              onChange={(e) => setDegree(e.target.value)}
              placeholder="Dr. iur., Dr. phil. …"
              className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
            />
          </label>
        </div>
        <label className="block space-y-1">
          <span className="text-[var(--muted)]">Hochschule</span>
          <input
            value={institution}
            onChange={(e) => setInstitution(e.target.value)}
            className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
          />
        </label>
        <label className="block space-y-1">
          <span className="text-[var(--muted)]">Person (optional)</span>
          <select
            value={personId}
            onChange={(e) => setPersonId(e.target.value)}
            className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
          >
            <option value="">— nicht zugeordnet —</option>
            {persons.map((p) => (
              <option key={p.id} value={p.id}>
                {p.display_name}
              </option>
            ))}
          </select>
        </label>
        <button
          type="submit"
          disabled={submitting}
          className="border border-[var(--rule)] px-4 py-1 hover:bg-[var(--rule)]/40 transition disabled:opacity-50"
        >
          {submitting ? "Lade hoch…" : "Einlesen"}
        </button>
        {error && <p className="text-[var(--accent)]">{error}</p>}
      </form>
    </section>
  );
}
