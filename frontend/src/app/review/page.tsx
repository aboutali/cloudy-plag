import Link from "next/link";
import { listDocuments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ReviewIndexPage() {
  const docs = await listDocuments().catch(() => []);
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-3xl tracking-tight">Review-Queue</h1>
        <p className="font-sans text-sm text-[var(--muted)] mt-1">
          Wählen Sie ein Dokument, um ungeprüfte Hinweise zu sichten.
        </p>
      </header>
      <ul className="divide-y divide-[var(--rule)] border-t border-b border-[var(--rule)]">
        {docs.map((d) => (
          <li key={d.id} className="py-3">
            <Link
              href={`/review/${d.id}`}
              className="block hover:bg-[var(--rule)]/30 -mx-4 px-4 py-2 transition"
            >
              <div className="flex items-baseline justify-between gap-6">
                <span>{d.title}</span>
                <span className="font-sans text-xs text-[var(--muted)] tabular-nums">
                  {d.year ?? "—"}
                </span>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
