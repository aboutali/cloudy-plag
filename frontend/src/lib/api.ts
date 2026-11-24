// Browser-side base URL (exposed via NEXT_PUBLIC_*).
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Server-side base URL — used by Server Components running inside the
// frontend container, where "localhost" is not the backend.
const INTERNAL_API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL ?? API_BASE_URL;

function apiBase(): string {
  return typeof window === "undefined" ? INTERNAL_API_BASE_URL : API_BASE_URL;
}

export type Document = {
  id: string;
  person_id: string | null;
  title: string;
  year: number | null;
  institution: string | null;
  degree: string | null;
  canonical_hash: string;
  provenance: Record<string, unknown>;
  created_at: string;
};

export type DocumentSpan = {
  id: string;
  page: number;
  bbox_x0: number;
  bbox_y0: number;
  bbox_x1: number;
  bbox_y1: number;
  text: string;
};

export type Person = {
  id: string;
  display_name: string;
  roles: string[] | null;
  legal_sensitivity_flag: boolean;
  right_of_reply_url: string | null;
  created_at: string;
};

export type PersonDetail = {
  person: Person;
  documents: Document[];
  documented_findings: number;
  findings_under_review: number;
};

export async function listPersons(): Promise<Person[]> {
  const res = await fetch(`${apiBase()}/persons`, { cache: "no-store" });
  if (!res.ok) throw new Error(`listPersons: ${res.status}`);
  return res.json();
}

export async function getPersonDetail(id: string): Promise<PersonDetail> {
  const res = await fetch(`${apiBase()}/persons/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`getPersonDetail: ${res.status}`);
  return res.json();
}

export async function createPerson(payload: {
  display_name: string;
  roles?: string[];
  right_of_reply_url?: string;
  legal_sensitivity_flag?: boolean;
}): Promise<Person> {
  const res = await fetch(`${API_BASE_URL}/persons`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`createPerson: ${res.status}`);
  return res.json();
}

export async function updatePerson(
  id: string,
  payload: {
    display_name?: string;
    roles?: string[];
    right_of_reply_url?: string | null;
    legal_sensitivity_flag?: boolean;
  },
): Promise<Person> {
  const res = await fetch(`${API_BASE_URL}/persons/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`updatePerson: ${res.status}`);
  return res.json();
}

export async function listDocuments(): Promise<Document[]> {
  const res = await fetch(`${apiBase()}/documents`, { cache: "no-store" });
  if (!res.ok) throw new Error(`listDocuments: ${res.status}`);
  return res.json();
}

export async function getDocument(id: string): Promise<Document> {
  const res = await fetch(`${apiBase()}/documents/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`getDocument: ${res.status}`);
  return res.json();
}

export async function getDocumentSpans(
  id: string,
  page?: number,
): Promise<DocumentSpan[]> {
  const url = new URL(`${apiBase()}/documents/${id}/spans`);
  if (page !== undefined) url.searchParams.set("page", String(page));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`getDocumentSpans: ${res.status}`);
  return res.json();
}

export type Finding = {
  id: string;
  document_span_id: string;
  source_span_ids: string[];
  kind: string;
  detector_id: string;
  detector_version: string;
  confidence_category: "requires_review" | "documented";
  status: "unreviewed" | "confirmed" | "rejected" | "disputed";
  rationale: string | null;
  created_at: string;
};

export type SourceSpan = {
  id: string;
  source_id: string;
  locator: string | null;
  text: string;
};

export type FindingDetail = {
  finding: Finding;
  document_span: DocumentSpan;
  source_spans: SourceSpan[];
};

export async function listDocumentFindings(
  documentId: string,
  statusFilter?: string,
): Promise<Finding[]> {
  const url = new URL(`${apiBase()}/documents/${documentId}/findings`);
  if (statusFilter) url.searchParams.set("status_filter", statusFilter);
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`listDocumentFindings: ${res.status}`);
  return res.json();
}

export async function getFindingDetail(id: string): Promise<FindingDetail> {
  // Called from both server (page) and client (panel) — apiBase picks the right one.
  const res = await fetch(`${apiBase()}/findings/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`getFindingDetail: ${res.status}`);
  return res.json();
}

export function documentPdfUrl(id: string): string {
  return `${API_BASE_URL}/documents/${id}/pdf`;
}

export type Source = {
  id: string;
  kind: string;
  title: string;
  authors: string[] | null;
  year: number | null;
  identifiers: Record<string, unknown>;
  canonical_hash: string;
  created_at: string;
};

export async function listSources(): Promise<Source[]> {
  const res = await fetch(`${apiBase()}/sources`, { cache: "no-store" });
  if (!res.ok) throw new Error(`listSources: ${res.status}`);
  return res.json();
}

export async function ingestSourceText(payload: {
  kind: string;
  title: string;
  text: string;
  authors?: string[];
  year?: number;
}): Promise<{ source: Source; span_count: number }> {
  const res = await fetch(`${API_BASE_URL}/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`ingestSourceText: ${res.status}`);
  return res.json();
}

export async function ingestDocumentFile(form: FormData): Promise<{
  document: Document;
  span_count: number;
}> {
  const res = await fetch(`${API_BASE_URL}/documents`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`ingestDocumentFile: ${res.status} ${text}`);
  }
  return res.json();
}

export async function runNgramDetector(
  documentId: string,
): Promise<{ analysis_run_id: string; findings_created: number }> {
  const res = await fetch(`${API_BASE_URL}/detectors/ngram/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId }),
  });
  if (!res.ok) throw new Error(`runNgramDetector: ${res.status}`);
  return res.json();
}

export async function runParaphraseDetector(
  documentId: string,
): Promise<{ analysis_run_id: string; findings_created: number }> {
  const res = await fetch(`${API_BASE_URL}/detectors/paraphrase/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId }),
  });
  if (!res.ok) throw new Error(`runParaphraseDetector: ${res.status}`);
  return res.json();
}

export async function ingestSourceUrl(payload: {
  url: string;
  kind?: string;
  title?: string;
  authors?: string[];
  year?: number;
}): Promise<{ source: Source; span_count: number }> {
  const res = await fetch(`${API_BASE_URL}/sources/from-url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`ingestSourceUrl: ${res.status}`);
  return res.json();
}

export type DnbCandidate = {
  title: string;
  authors: string[];
  year: string | null;
  institution: string | null;
  urn: string | null;
  resolver_url: string | null;
  record_id: string | null;
};

export async function dnbSearch(name: string, limit = 10): Promise<DnbCandidate[]> {
  const url = new URL(`${apiBase()}/dnb/search`);
  url.searchParams.set("name", name);
  url.searchParams.set("limit", String(limit));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`dnbSearch: ${res.status}`);
  return res.json();
}

export type AuditEvent = {
  id: string;
  occurred_at: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  payload: Record<string, unknown>;
};

export async function listAuditEvents(params?: {
  entity_type?: string;
  entity_id?: string;
  limit?: number;
}): Promise<AuditEvent[]> {
  const url = new URL(`${apiBase()}/audit/events`);
  if (params?.entity_type) url.searchParams.set("entity_type", params.entity_type);
  if (params?.entity_id) url.searchParams.set("entity_id", params.entity_id);
  if (params?.limit) url.searchParams.set("limit", String(params.limit));
  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`listAuditEvents: ${res.status}`);
  return res.json();
}
