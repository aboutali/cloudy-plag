export default function AboutPage() {
  return (
    <article className="prose-base max-w-2xl space-y-4">
      <h1 className="text-3xl tracking-tight">Über cloudy-plag</h1>
      <p className="leading-relaxed">
        cloudy-plag ist ein dokumentarisches Projekt in der Tradition von
        VroniPlag Wiki, neu gedacht für die Möglichkeiten und Risiken
        generativer KI. Wir prüfen Dissertationen öffentlicher Personen entlang
        dreier Achsen: ungeklärte Übernahmen, Originalität der Argumente und
        methodische Sorgfalt.
      </p>
      <p className="leading-relaxed">
        Jede Fundstelle ist nachvollziehbar belegt. Modelle erzeugen Hinweise.
        Veröffentlicht wird ausschließlich, was von menschlichen
        Gutachterinnen und Gutachtern bestätigt wurde.
      </p>
      <p className="leading-relaxed text-[var(--muted)]">
        Diese Plattform spricht keine Urteile aus. Begriffe wie „Plagiat" sind
        Behörden und Gerichten vorbehalten.
      </p>
    </article>
  );
}
