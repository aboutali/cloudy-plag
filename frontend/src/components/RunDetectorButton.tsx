"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { runNgramDetector, runParaphraseDetector } from "@/lib/api";

type DetectorKind = "ngram" | "paraphrase";

export function RunDetectorButton({ documentId }: { documentId: string }) {
  const router = useRouter();
  const [running, setRunning] = useState<DetectorKind | null>(null);
  const [result, setResult] = useState<string | null>(null);

  async function go(kind: DetectorKind) {
    setRunning(kind);
    setResult(null);
    try {
      const r = await (kind === "ngram"
        ? runNgramDetector(documentId)
        : runParaphraseDetector(documentId));
      setResult(`${kind}: ${r.findings_created} Hinweise erzeugt.`);
      router.refresh();
    } catch (e) {
      setResult(e instanceof Error ? e.message : "Fehler");
    } finally {
      setRunning(null);
    }
  }

  return (
    <div className="flex items-center gap-3 font-sans text-sm flex-wrap">
      <button
        type="button"
        onClick={() => go("ngram")}
        disabled={running !== null}
        className="border border-[var(--rule)] px-3 py-1 hover:bg-[var(--rule)]/40 transition disabled:opacity-50"
      >
        {running === "ngram" ? "Läuft…" : "n-Gram-Detektor"}
      </button>
      <button
        type="button"
        onClick={() => go("paraphrase")}
        disabled={running !== null}
        className="border border-[var(--rule)] px-3 py-1 hover:bg-[var(--rule)]/40 transition disabled:opacity-50"
      >
        {running === "paraphrase" ? "Läuft…" : "Paraphrasen-Detektor"}
      </button>
      {result && <span className="text-[var(--muted)] text-xs">{result}</span>}
    </div>
  );
}
