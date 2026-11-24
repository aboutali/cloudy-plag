"use client";

import { useEffect, useRef, useState } from "react";

type PdfBox = {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
};

type Highlight = PdfBox & {
  id: string;
  status: "documented" | "requires_review";
  active?: boolean;
};

type Props = {
  pdfUrl: string;
  page: number;
  highlights: Highlight[];
  onHighlightClick?: (id: string) => void;
};

export function PdfPageWithOverlays({
  pdfUrl,
  page,
  highlights,
  onHighlightClick,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [pageSize, setPageSize] = useState<{ w: number; h: number; scale: number } | null>(
    null,
  );
  const [pdfPageHeight, setPdfPageHeight] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function render() {
      try {
        const pdfjs = await import("pdfjs-dist");
        // Use the bundled worker via a Blob URL — avoids hosting concerns in dev.
        const worker = await import("pdfjs-dist/build/pdf.worker.mjs?url" as string).catch(
          () => null,
        );
        if (worker && (worker as { default?: string }).default) {
          pdfjs.GlobalWorkerOptions.workerSrc = (worker as { default: string }).default;
        } else {
          // Fallback: disable worker (slow but works in dev).
          pdfjs.GlobalWorkerOptions.workerSrc = "";
        }

        const loadingTask = pdfjs.getDocument({ url: pdfUrl, withCredentials: false });
        const doc = await loadingTask.promise;
        if (cancelled) return;
        const pdfPage = await doc.getPage(page);
        if (cancelled) return;

        const viewport = pdfPage.getViewport({ scale: 1.5 });
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        await pdfPage.render({ canvasContext: ctx, viewport }).promise;
        if (cancelled) return;
        setPageSize({ w: viewport.width, h: viewport.height, scale: 1.5 });
        setPdfPageHeight(pdfPage.view[3] - pdfPage.view[1]);
      } catch (e) {
        setError(e instanceof Error ? e.message : "PDF render failed");
      }
    }
    render();
    return () => {
      cancelled = true;
    };
  }, [pdfUrl, page]);

  return (
    <div ref={containerRef} className="relative inline-block">
      <canvas ref={canvasRef} className="block shadow-sm" />
      {error && (
        <p className="font-sans text-xs text-[var(--accent)] absolute top-2 left-2 bg-white/80 px-2 py-1">
          {error}
        </p>
      )}
      {pageSize && pdfPageHeight !== null && (
        <div className="absolute inset-0 pointer-events-none">
          {highlights.map((h) => {
            const left = h.x0 * pageSize.scale;
            // pdfplumber's y origin is top-left; PDF.js viewport is also top-left at scale 1.5.
            const top = h.y0 * pageSize.scale;
            const width = (h.x1 - h.x0) * pageSize.scale;
            const height = (h.y1 - h.y0) * pageSize.scale;
            const color =
              h.status === "documented"
                ? "rgba(122, 28, 28, 0.22)"
                : "rgba(180, 140, 30, 0.22)";
            const border =
              h.status === "documented" ? "rgb(122, 28, 28)" : "rgb(180, 140, 30)";
            return (
              <button
                key={h.id}
                type="button"
                onClick={() => onHighlightClick?.(h.id)}
                className="absolute pointer-events-auto cursor-pointer transition hover:brightness-95"
                style={{
                  left,
                  top,
                  width,
                  height,
                  background: color,
                  outline: `1px solid ${border}`,
                  outlineOffset: h.active ? 1 : 0,
                  boxShadow: h.active ? `0 0 0 2px ${border}` : "none",
                }}
                aria-label={`Fundstelle ${h.id}`}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
