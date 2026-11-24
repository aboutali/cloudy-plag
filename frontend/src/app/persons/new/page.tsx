"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createPerson } from "@/lib/api";

export default function NewPersonPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [roles, setRoles] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const person = await createPerson({
        display_name: displayName,
        roles: roles
          ? roles.split(",").map((r) => r.trim()).filter(Boolean)
          : undefined,
      });
      router.push(`/persons/${person.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-6 max-w-xl">
      <header>
        <h1 className="text-3xl tracking-tight">Person anlegen</h1>
        <p className="font-sans text-sm text-[var(--muted)] mt-1">
          Erfassen Sie öffentliche Personen, deren Dissertation Gegenstand der
          Prüfung ist.
        </p>
      </header>
      <form onSubmit={submit} className="space-y-4 font-sans text-sm">
        <label className="block space-y-1">
          <span className="text-[var(--muted)]">Anzeigename</span>
          <input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
            className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
          />
        </label>
        <label className="block space-y-1">
          <span className="text-[var(--muted)]">
            Öffentliche Rollen (kommagetrennt)
          </span>
          <input
            value={roles}
            onChange={(e) => setRoles(e.target.value)}
            placeholder="z. B. Bundestagsabgeordnete, Ministerin"
            className="w-full border border-[var(--rule)] px-2 py-1 bg-transparent"
          />
        </label>
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="border border-[var(--rule)] px-4 py-1 hover:bg-[var(--rule)]/40 transition disabled:opacity-50"
          >
            {submitting ? "Speichere…" : "Anlegen"}
          </button>
        </div>
        {error && <p className="text-[var(--accent)]">{error}</p>}
      </form>
    </section>
  );
}
