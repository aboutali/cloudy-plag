import Link from "next/link";

export default function HomePage() {
  return (
    <article className="prose-base max-w-2xl space-y-6">
      <h1 className="text-4xl tracking-tight">
        Dissertationen, geprüft im GenAI-Zeitalter.
      </h1>
      <p className="text-lg leading-relaxed text-[var(--foreground)]/90">
        cloudy-plag dokumentiert Hinweise auf{" "}
        <em>ungeklärte Übernahmen</em>, fragwürdige Originalität und
        methodische Schwächen in den Dissertationen öffentlicher Personen —
        nachvollziehbar belegt, von Menschen geprüft, nie allein durch ein
        Modell veröffentlicht.
      </p>
      <p className="text-base leading-relaxed text-[var(--muted)]">
        Jede Fundstelle verweist auf die Primärquelle. Jede Veröffentlichung
        wird redaktionell bestätigt. KI erzeugt Hinweise, nicht Urteile.
      </p>
      <div className="pt-4 font-sans text-sm">
        <Link
          href="/documents"
          className="inline-block border border-[var(--rule)] px-4 py-2 hover:bg-[var(--rule)]/40 transition"
        >
          Dokumente ansehen →
        </Link>
      </div>
    </article>
  );
}
