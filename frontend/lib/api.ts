// Thin typed client for the Engram backend.
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export interface SkillStep {
  id: string; type: string; title: string; produces?: string;
  tool?: string; action?: string; requires_approval: boolean;
  consumes?: string[]; decision_ref?: string;
}
export interface Guard { id: string; description: string; action?: string; requires_approval: boolean; }
export interface Skill {
  id?: string; name: string; goal: string; description: string; version: number;
  confidence: number; freshness: number;
  inputs: { name: string; description?: string }[];
  steps: SkillStep[]; guards: Guard[];
  provenance: { node_ids: string[]; sources: string[] };
}
export interface SkillSummary { id: string; name: string; goal: string; confidence: number; freshness: number; }
export interface Execution {
  id: string; status: string; outcome?: string;
  pending?: { action: string; reason: string; triggered_guards: string[] };
  trace: { step_id: string; type: string; detail: any }[];
  approval_id?: string;
}

export const SAMPLE_REFUND_DOC = `Refund Policy - Customer Success Wiki (last reviewed 20 days ago)

Customers on a paid plan may request a refund. Support evaluates each request:
- If the subscription has been active for at least 12 months AND the customer's lifetime value is at least $10,000, support may AUTO-APPROVE the refund.
- If the account has a chargeback or fraud flag, the request must be ESCALATED to the Finance team and must never be auto-approved.
- Anything else goes to MANUAL REVIEW by a support lead.
Exception: refunds of $5,000 or more always require explicit Finance approval.
The Refund Policy is owned and approved by the Finance team.`;

export const api = {
  createCompany: (name: string) => j<{ id: string }>("/companies", { method: "POST", body: JSON.stringify({ name }) }),
  ingest: (cid: string, text: string) => j<{ nodes_created: string[] }>(`/companies/${cid}/ingest`, { method: "POST", body: JSON.stringify({ text }) }),
  generate: (cid: string, goal: string) => j<Skill>(`/companies/${cid}/skills/generate`, { method: "POST", body: JSON.stringify({ goal }) }),
  listSkills: (cid: string) => j<SkillSummary[]>(`/companies/${cid}/skills`),
  getSkill: (sid: string) => j<Skill>(`/skills/${sid}`),
  execute: (sid: string, inputs: Record<string, unknown>) => j<Execution>(`/skills/${sid}/execute`, { method: "POST", body: JSON.stringify({ inputs }) }),
  decide: (aid: string, body: { decision: string; action?: string; reason?: string; decided_by?: string }) =>
    j<Execution>(`/approvals/${aid}/decision`, { method: "POST", body: JSON.stringify(body) }),
};
