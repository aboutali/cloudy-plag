import { notFound } from "next/navigation";
import { getDocument, listDocumentFindings } from "@/lib/api";
import { ReviewQueue } from "@/components/ReviewQueue";

export const dynamic = "force-dynamic";

export default async function ReviewDocumentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let doc: Awaited<ReturnType<typeof getDocument>>;
  try {
    doc = await getDocument(id);
  } catch {
    notFound();
  }
  const findings = await listDocumentFindings(id, "unreviewed");
  return (
    <section className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl tracking-tight">Review · {doc.title}</h1>
        <p className="font-sans text-sm text-[var(--muted)]">
          {findings.length} ungeprüfte Hinweise. Bestätigen Sie nur, was Sie an
          den Primärquellen geprüft haben.
        </p>
      </header>
      <ReviewQueue findings={findings} />
    </section>
  );
}
