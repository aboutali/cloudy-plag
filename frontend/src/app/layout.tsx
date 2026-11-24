import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "cloudy-plag",
  description:
    "Dokumentation — keine Anschuldigung. Dissertationen öffentlicher Personen, geprüft auf Originalität, Rigor und Übernahmen.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body className="font-serif antialiased">
        <header className="border-b border-[var(--rule)]">
          <div className="mx-auto max-w-5xl px-6 py-6 flex items-baseline justify-between">
            <Link href="/" className="text-xl tracking-tight">
              <span className="text-[var(--accent)]">cloudy</span>
              <span className="text-[var(--muted)]">·</span>
              <span>plag</span>
            </Link>
            <nav className="text-sm text-[var(--muted)] space-x-6 font-sans">
              <Link href="/persons">Personen</Link>
              <Link href="/documents">Dokumente</Link>
              <Link href="/sources">Quellen</Link>
              <Link href="/review">Review</Link>
              <Link href="/dnb">DNB</Link>
              <Link href="/audit">Audit</Link>
              <Link href="/about">Über</Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
        <footer className="border-t border-[var(--rule)] mt-20">
          <div className="mx-auto max-w-5xl px-6 py-6 text-xs text-[var(--muted)] font-sans">
            Diese Seite dokumentiert Beobachtungen, keine Urteile. Findings sind
            Hinweise, keine Plagiatsfeststellungen.
          </div>
        </footer>
      </body>
    </html>
  );
}
