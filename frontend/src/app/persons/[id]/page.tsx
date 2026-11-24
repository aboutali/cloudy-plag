import Link from "next/link";
import { notFound } from "next/navigation";
import { getPersonDetail } from "@/lib/api";
import { RightOfReplyEditor } from "@/components/RightOfReplyEditor";
import { AuditTimeline } from "@/components/AuditTimeline";

export const dynamic = "force-dynamic";

export default async function PersonDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let detail;
  try {
    detail = await getPersonDetail(id);
  } catch {
    notFound();
  }
  const { person, documents, documented_findings, findings_under_review } = detail;

  return (
    <article className="space-y-10">
      <header className="space-y-2 border-b border-[var(--rule)] pb-6">
        <h1 className="text-3xl tracking-tight">{person.display_name}</h1>
        {person.roles && person.roles.length > 0 && (
          <div className="font-sans text-sm text-[var(--muted)]">
            {person.roles.join(" · ")}
          </div>
        )}
        <div className="flex gap-6 pt-2 font-sans text-xs text-[var(--muted)]">
          <span>
            <strong className="text-[var(--accent)]">{documented_findings}</strong>{" "}
            dokumentierte Findings
          </span>
          <span>
            <strong>{findings_under_review}</strong> Hinweise unter Prüfung
          </span>
        </div>
      </header>

      <section className="space-y-3">
        <h2 className="text-lg tracking-tight">Dissertation(en)</h2>
        {documents.length === 0 && (
          <p className="font-sans text-sm text-[var(--muted)]">
            Noch keine Dissertation verknüpft.
          </p>
        )}
        <ul className="divide-y divide-[var(--rule)] border-t border-b border-[var(--rule)]">
          {documents.map((d) => (
            <li key={d.id} className="py-3">
              <Link
                href={`/documents/${d.id}`}
                className="block hover:bg-[var(--rule)]/30 -mx-4 px-4 py-2 transition"
              >
                <div className="flex items-baseline justify-between gap-6">
                  <span>{d.title}</span>
                  <span className="font-sans text-xs text-[var(--muted)]">
                    {d.year ?? "—"} · {d.institution ?? "—"}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg tracking-tight">Stellungnahme der Person</h2>
        <p className="font-sans text-xs text-[var(--muted)]">
          Jede dokumentierte Person erhält die Möglichkeit zur Gegendarstellung.
          Verknüpfen Sie hier eine veröffentlichte Stellungnahme.
        </p>
        <RightOfReplyEditor
          personId={person.id}
          initialUrl={person.right_of_reply_url}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg tracking-tight">Verlauf</h2>
        <AuditTimeline entityType="person" entityId={person.id} />
      </section>
    </article>
  );
}
