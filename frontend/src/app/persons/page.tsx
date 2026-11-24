import Link from "next/link";
import { listPersons } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function PersonsPage() {
  const persons = await listPersons().catch(() => []);
  return (
    <section className="space-y-8">
      <header className="flex items-end justify-between gap-6">
        <div>
          <h1 className="text-3xl tracking-tight">Personen</h1>
          <p className="font-sans text-sm text-[var(--muted)] mt-1">
            Öffentliche Personen, deren Dissertationen geprüft werden.
          </p>
        </div>
        <Link
          href="/persons/new"
          className="font-sans text-sm border border-[var(--rule)] px-3 py-1 hover:bg-[var(--rule)]/40 transition"
        >
          + Person anlegen
        </Link>
      </header>

      {persons.length === 0 && (
        <p className="font-sans text-sm text-[var(--muted)]">
          Noch keine Personen erfasst.
        </p>
      )}

      <ul className="divide-y divide-[var(--rule)] border-t border-b border-[var(--rule)]">
        {persons.map((p) => (
          <li key={p.id} className="py-4">
            <Link
              href={`/persons/${p.id}`}
              className="block hover:bg-[var(--rule)]/30 -mx-4 px-4 py-2 transition"
            >
              <div className="flex items-baseline justify-between gap-6">
                <h2 className="text-lg">{p.display_name}</h2>
                {p.roles && p.roles.length > 0 && (
                  <span className="font-sans text-xs text-[var(--muted)]">
                    {p.roles.join(" · ")}
                  </span>
                )}
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
