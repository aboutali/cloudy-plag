import { notFound } from "next/navigation";
import {
  getDocument,
  getDocumentSpans,
  listDocumentFindings,
} from "@/lib/api";
import { SideBySide } from "@/components/SideBySide";
import { RunDetectorButton } from "@/components/RunDetectorButton";
import { AuditTimeline } from "@/components/AuditTimeline";

export const dynamic = "force-dynamic";

export default async function DocumentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let document: Awaited<ReturnType<typeof getDocument>>;
  try {
    document = await getDocument(id);
  } catch {
    notFound();
  }

  const [spans, findings] = await Promise.all([
    getDocumentSpans(id),
    listDocumentFindings(id),
  ]);

  return (
    <article className="space-y-10">
      <header className="space-y-2 border-b border-[var(--rule)] pb-6">
        <h1 className="text-3xl tracking-tight">{document.title}</h1>
        <div className="font-sans text-sm text-[var(--muted)]">
          {[document.institution, document.degree, document.year]
            .filter(Boolean)
            .join(" · ") || "—"}
        </div>
        <div className="font-sans text-xs text-[var(--muted)] pt-2">
          SHA-256: <code className="break-all">{document.canonical_hash}</code>
        </div>
      </header>

      <section className="space-y-4">
        <div className="flex items-baseline justify-between gap-4">
          <h2 className="text-lg tracking-tight">Side-by-Side</h2>
          <RunDetectorButton documentId={id} />
        </div>
        <SideBySide documentId={id} spans={spans} findings={findings} />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg tracking-tight">Verlauf</h2>
        <AuditTimeline entityType="document" entityId={id} />
      </section>
    </article>
  );
}
