"use client";

import { useState } from "react";
import { updatePerson } from "@/lib/api";

export function RightOfReplyEditor({
  personId,
  initialUrl,
}: {
  personId: string;
  initialUrl: string | null;
}) {
  const [url, setUrl] = useState(initialUrl ?? "");
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      await updatePerson(personId, { right_of_reply_url: url || null });
      setSavedAt(Date.now());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-3">
      {url && (
        <p className="text-sm">
          Aktuell verlinkt:{" "}
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[var(--accent)] underline"
          >
            {url}
          </a>
        </p>
      )}
      <div className="flex gap-2 items-center font-sans text-sm">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://…"
          className="flex-1 border border-[var(--rule)] px-2 py-1 bg-transparent"
        />
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="border border-[var(--rule)] px-3 py-1 hover:bg-[var(--rule)]/40 transition disabled:opacity-50"
        >
          {saving ? "Speichere…" : "Speichern"}
        </button>
      </div>
      {savedAt && (
        <p className="font-sans text-xs text-[var(--muted)]">Gespeichert.</p>
      )}
      {error && (
        <p className="font-sans text-xs text-[var(--accent)]">{error}</p>
      )}
    </div>
  );
}
