"use client";
import { useState } from "react";
import { api, type Execution } from "@/lib/api";
import { Card, Button, Badge } from "@/components/ui";

const SAMPLES = ["cust_loyal", "cust_fraud", "cust_highvalue", "cust_new"];

export default function Executions() {
  const [sid, setSid] = useState("");
  const [customer, setCustomer] = useState("cust_loyal");
  const [exec, setExec] = useState<Execution | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setErr(null);
    try { setExec(await api.execute(sid, { customer_id: customer })); }
    catch (e: any) { setErr(e.message); }
  }
  async function decide(decision: string, action?: string) {
    if (!exec?.approval_id) return;
    try { setExec(await api.decide(exec.approval_id, { decision, action, decided_by: "you@acme.com", reason: "reviewed" })); }
    catch (e: any) { setErr(e.message); }
  }

  const tone = exec?.status === "completed" ? "green" : exec?.status === "pending_approval" ? "amber" : "rose";

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Run a skill</h1>
      <Card className="space-y-3">
        <label className="block text-sm">Skill ID
          <input value={sid} onChange={(e) => setSid(e.target.value)} placeholder="skill_xxxxxxxx"
            className="mt-1 w-full rounded-lg border px-3 py-1.5 text-sm font-mono" />
        </label>
        <label className="block text-sm">Customer
          <select value={customer} onChange={(e) => setCustomer(e.target.value)}
            className="mt-1 w-full rounded-lg border px-3 py-1.5 text-sm">
            {SAMPLES.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <Button onClick={run} disabled={!sid}>Execute</Button>
      </Card>

      {err && <p className="text-rose-600">Error: {err}</p>}

      {exec && (
        <Card className="space-y-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm">{exec.id}</span>
            <Badge tone={tone as any}>{exec.status}</Badge>
            {exec.outcome && <Badge tone="indigo">outcome: {exec.outcome}</Badge>}
          </div>

          {exec.status === "pending_approval" && exec.pending && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
              <p className="text-sm">Wants to <b>{exec.pending.action}</b> — {exec.pending.reason}</p>
              {exec.pending.triggered_guards.length > 0 &&
                <p className="mt-1 text-xs text-slate-500">guards: {exec.pending.triggered_guards.join(", ")}</p>}
              <div className="mt-2 flex gap-2">
                <Button onClick={() => decide("approve")}>Approve</Button>
                <Button variant="danger" onClick={() => decide("override", "deny_refund")}>Override → deny</Button>
              </div>
            </div>
          )}

          <details>
            <summary className="cursor-pointer text-sm text-slate-600">Execution trace ({exec.trace.length} steps)</summary>
            <pre className="mt-2 overflow-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-100">
{JSON.stringify(exec.trace, null, 2)}</pre>
          </details>
        </Card>
      )}
    </div>
  );
}
