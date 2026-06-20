"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api, SAMPLE_REFUND_DOC, type SkillSummary, type Execution } from "@/lib/api";
import { Card, Badge, ConfidenceBar } from "@/components/ui";
import { EngramMark } from "@/components/logo";
import {
  Sparkles, ArrowRight, Network, Workflow, ShieldCheck, Activity,
  Mail, MessageSquare, GitBranch, Database, Users, CheckCircle2,
  Loader2, AlertTriangle, BookOpen, Hand, FileText,
} from "lucide-react";

const CONNECTORS = [
  { name: "Mail", icon: Mail, note: "Approvals & customer commitments" },
  { name: "Slack", icon: MessageSquare, note: "Decisions made in threads" },
  { name: "Jira", icon: GitBranch, note: "How work is triaged & routed" },
  { name: "CRM", icon: Database, note: "Account tiers, owners, history" },
];

const STAGES = [
  { label: "Ingest policy", sub: "extract knowledge nodes" },
  { label: "Compile skill", sub: "graph to runnable workflow" },
  { label: "Execute", sub: "run on a live account" },
  { label: "Human decision", sub: "approve or override" },
];

/* Decorative neural-graph motif for the header */
function BrainGraph() {
  const nodes: [number, number][] = [
    [36, 86], [104, 42], [104, 126], [178, 70], [178, 132], [252, 50], [252, 112], [320, 84],
  ];
  const edges: [number, number][] = [
    [0, 1], [0, 2], [1, 3], [2, 3], [2, 4], [3, 5], [3, 6], [4, 6], [5, 7], [6, 7],
  ];
  const colors = ["#22d3ee", "#7c3aed", "#6366f1"];
  return (
    <svg viewBox="0 0 360 170" className="h-full w-full" aria-hidden="true">
      <g stroke="#6366f1" strokeWidth="1">
        {edges.map(([a, b], i) => (
          <line key={i} className="eg-edge" x1={nodes[a][0]} y1={nodes[a][1]} x2={nodes[b][0]} y2={nodes[b][1]} style={{ animationDelay: `${i * 0.2}s` }} />
        ))}
      </g>
      {nodes.map(([x, y], i) => (
        <circle key={i} className="eg-node" cx={x} cy={y} r={i % 4 === 0 ? 5 : 3.5} fill={colors[i % 3]} style={{ animationDelay: `${i * 0.35}s` }} />
      ))}
    </svg>
  );
}

function useCountUp(target: number, ms = 800) {
  const [n, setN] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const from = n;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / ms);
      const eased = 1 - Math.pow(1 - p, 3);
      setN(Math.round(from + (target - from) * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]); // eslint-disable-line react-hooks/exhaustive-deps
  return n;
}

function Stat({
  icon: Icon, label, value, suffix = "", hint, tone = "indigo", ready,
}: {
  icon: any; label: string; value: number; suffix?: string; hint?: string;
  tone?: "indigo" | "amber" | "emerald" | "slate"; ready: boolean;
}) {
  const n = useCountUp(value);
  const ring = {
    indigo: "bg-indigo-50 text-indigo-600",
    amber: "bg-amber-50 text-amber-600",
    emerald: "bg-emerald-50 text-emerald-600",
    slate: "bg-slate-100 text-slate-500",
  }[tone];
  return (
    <div className="animate-fade-up rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex items-center gap-2">
        <span className={`grid h-8 w-8 place-items-center rounded-lg ${ring}`}><Icon className="h-4 w-4" /></span>
        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</span>
      </div>
      <div className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">{ready ? `${n}${suffix}` : "—"}</div>
      {hint && <div className="mt-0.5 text-xs text-slate-400">{hint}</div>}
    </div>
  );
}

function Pipeline({ active, awaiting }: { active: number; awaiting: boolean }) {
  return (
    <ol className="space-y-1">
      {STAGES.map((st, i) => {
        const done = active === 4 || i < active;
        const isActive = i === active && active !== 4;
        const waiting = isActive && i === 3 && awaiting;
        const running = isActive && !waiting;
        return (
          <li key={st.label} className={`flex items-center gap-3 rounded-lg px-2 py-1.5 transition ${isActive ? "bg-slate-50" : ""}`}>
            <span className="grid h-7 w-7 shrink-0 place-items-center">
              {done ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
              ) : waiting ? (
                <Hand className="h-5 w-5 text-amber-500" />
              ) : running ? (
                <Loader2 className="h-5 w-5 animate-spin text-indigo-600" />
              ) : (
                <span className="grid h-6 w-6 place-items-center rounded-full border text-xs font-medium text-slate-400">{i + 1}</span>
              )}
            </span>
            <div className="min-w-0 flex-1">
              <div className={`text-sm font-medium ${done ? "text-slate-800" : isActive ? "text-slate-900" : "text-slate-400"}`}>{st.label}</div>
              <div className="text-xs text-slate-400">{st.sub}</div>
            </div>
            {waiting && <span className="shrink-0 text-xs font-medium text-amber-600">waiting on you</span>}
          </li>
        );
      })}
    </ol>
  );
}

export default function Dashboard() {
  const [cid, setCid] = useState<string | null>(null);
  const [nodes, setNodes] = useState(0);
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [exec, setExec] = useState<Execution | null>(null);
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState("");
  const [active, setActive] = useState(-1);
  const [log, setLog] = useState<string[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const push = (m: string) => setLog((l) => [...l, m]);

  async function runLoop() {
    setBusy(true); setErr(null); setLog([]); setExec(null); setActive(0);
    try {
      setStage("Creating tenant");
      const { id } = await api.createCompany("Acme Inc.");
      setCid(id); push(`Created tenant ${id}`);

      setStage("Ingesting policy");
      const ing = await api.ingest(id, SAMPLE_REFUND_DOC);
      setNodes(ing.nodes_created.length);
      push(`Ingested refund policy -> ${ing.nodes_created.length} knowledge nodes`);
      setActive(1);

      setStage("Compiling skill");
      const skill = await api.generate(id, "refund_customer");
      push(`Compiled skill "${skill.name}" (confidence ${(skill.confidence * 100).toFixed(0)}%)`);
      const list = await api.listSkills(id);
      setSkills(list);
      setActive(2);

      if (skill.id) {
        setStage("Running on a flagged account");
        const e = await api.execute(skill.id, { customer_id: "cust_fraud" });
        setExec(e);
        if (e.status === "pending_approval") {
          push("Execution paused -> awaiting human approval");
          setActive(3);
        } else {
          push(`Execution ${e.status}${e.outcome ? ` -> ${e.outcome}` : ""}`);
          setActive(4);
        }
      } else {
        setActive(4);
      }
      setStage("");
    } catch (e: any) { setErr(e.message); push(`Error: ${e.message}`); setActive(-1); }
    setBusy(false);
  }

  async function decide(decision: string, action?: string) {
    if (!exec?.approval_id) return;
    try {
      const e = await api.decide(exec.approval_id, {
        decision, action, decided_by: "you@acme.com", reason: "reviewed in dashboard",
      });
      setExec(e);
      setActive(4);
      push(decision === "approve" ? "Approved -> agent completed the run" : "Overridden -> correction recorded");
    } catch (e: any) { setErr(e.message); }
  }

  const avgConf = useMemo(
    () => (skills.length ? Math.round((skills.reduce((s, k) => s + k.confidence, 0) / skills.length) * 100) : 0),
    [skills],
  );
  const pending = exec?.status === "pending_approval" ? 1 : 0;
  const initialized = cid !== null;

  return (
    <div className="space-y-6">
      {/* Command header */}
      <div className="relative overflow-hidden rounded-2xl bg-[#0B1020] px-7 py-6">
        <div className="pointer-events-none absolute right-2 top-1/2 hidden h-36 w-[360px] -translate-y-1/2 opacity-40 md:block">
          <BrainGraph />
        </div>
        <div className="relative flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <EngramMark className="h-7 w-7" />
              <span className="text-xl font-semibold tracking-tight text-white">Your company brain</span>
            </div>
            <div className="mt-1.5 flex items-center gap-2 text-sm text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                </span>
                Live
              </span>
              <span className="text-slate-600">·</span>
              <span className="font-mono text-xs">{initialized ? cid : "connected to Engram API"}</span>
            </div>
          </div>
          <button
            onClick={runLoop}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-900/30 ring-1 ring-white/10 transition hover:bg-indigo-500 disabled:opacity-60"
          >
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {busy ? `${stage || "Working"}…` : initialized ? "Re-run the brain" : "Run the brain"}
          </button>
        </div>
      </div>

      {err && (
        <div className="flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm text-rose-700">
          <AlertTriangle className="h-4 w-4 shrink-0" /> {err}
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat icon={Network} label="Knowledge nodes" value={nodes} hint="ingested from sources" ready={initialized} />
        <Stat icon={Workflow} label="Skills live" value={skills.length} hint="compiled & runnable" ready={initialized} />
        <Stat icon={ShieldCheck} label="Avg confidence" value={avgConf} suffix="%" hint="across all skills" tone="emerald" ready={initialized} />
        <Stat icon={Activity} label="Approvals waiting" value={pending} hint={pending ? "needs your review" : "all clear"} tone={pending ? "amber" : "slate"} ready={initialized} />
      </div>

      {/* Main grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column */}
        <div className="space-y-6 lg:col-span-2">
          {/* Command card with live pipeline */}
          <Card className="animate-fade-up">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="font-semibold text-slate-900">Teach your brain</h2>
                <p className="mt-0.5 text-sm text-slate-500">
                  One run takes a real policy from text to a guarded, executable skill — and hands you the decision.
                </p>
              </div>
              <Badge tone={busy ? "amber" : initialized ? "green" : "slate"}>
                {busy ? "running" : initialized ? "ready" : "idle"}
              </Badge>
            </div>

            <div className="mt-4 rounded-xl border bg-slate-50/60 p-3">
              <Pipeline active={active} awaiting={pending > 0} />
            </div>

            <details className="mt-3 rounded-lg border bg-white p-3">
              <summary className="flex cursor-pointer items-center gap-2 text-xs font-medium text-slate-500">
                <FileText className="h-3.5 w-3.5" /> Source · refund-policy.txt
              </summary>
              <pre className="mt-2 whitespace-pre-wrap text-xs leading-relaxed text-slate-600">{SAMPLE_REFUND_DOC}</pre>
            </details>

            {log.length > 0 && (
              <details className="mt-3 rounded-lg border bg-white p-3" open>
                <summary className="cursor-pointer text-xs font-medium text-slate-500">Live trace</summary>
                <pre className="mt-2 overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs leading-relaxed text-slate-100">{log.join("\n")}</pre>
              </details>
            )}
          </Card>

          {/* Skills library */}
          <Card className="animate-fade-up">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-slate-900">Skills library</h2>
              {skills.length > 0 && <span className="text-xs text-slate-400">{skills.length} compiled</span>}
            </div>
            {skills.length > 0 ? (
              <div className="mt-3 space-y-2.5">
                {skills.map((s) => {
                  const live = s.confidence >= 0.8;
                  return (
                    <div key={s.id} className="group flex items-center justify-between rounded-lg border p-3 transition hover:border-indigo-200 hover:shadow-sm">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-indigo-50 text-indigo-600"><Workflow className="h-4 w-4" /></span>
                          <span className="font-mono text-sm text-slate-800">{s.name}</span>
                          <Badge tone="indigo">{s.goal}</Badge>
                          <Badge tone={live ? "green" : "amber"}>{live ? "live" : "review"}</Badge>
                        </div>
                        <div className="mt-2 flex items-center gap-4">
                          <ConfidenceBar value={s.confidence} />
                          <span className="text-xs text-slate-400">freshness {Math.round(s.freshness * 100)}%</span>
                        </div>
                      </div>
                      <Link href={`/skills/${s.id}`} className="ml-3 inline-flex shrink-0 items-center gap-1 text-sm font-medium text-indigo-600 hover:underline">
                        View <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
                      </Link>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="mt-3 rounded-lg border border-dashed px-4 py-8 text-center text-sm text-slate-400">
                No skills yet. Run the brain to compile your first one.
              </div>
            )}
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Approvals inbox */}
          <Card className="animate-fade-up">
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 font-semibold text-slate-900"><Hand className="h-4 w-4 text-amber-500" /> Approvals</h2>
              {pending > 0 && <Badge tone="amber">{pending} waiting</Badge>}
            </div>

            {exec?.status === "pending_approval" && exec.pending ? (
              <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span className="rounded bg-white px-1.5 py-0.5 font-mono text-slate-600">account · cust_fraud</span>
                </div>
                <div className="mt-2 text-sm text-slate-700">
                  Agent wants to <strong className="font-medium">{exec.pending.action}</strong>
                </div>
                <p className="mt-1 text-xs text-slate-500">{exec.pending.reason}</p>
                {exec.pending.triggered_guards.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {exec.pending.triggered_guards.map((g) => (
                      <span key={g} className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800">{g}</span>
                    ))}
                  </div>
                )}
                <div className="mt-3 flex gap-2">
                  <button onClick={() => decide("approve")} className="flex-1 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-indigo-500">Approve</button>
                  <button onClick={() => decide("override", "deny_refund")} className="flex-1 rounded-lg border bg-white px-3 py-1.5 text-sm text-slate-700 transition hover:bg-slate-50">Override</button>
                </div>
              </div>
            ) : exec ? (
              <div className="mt-3 flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-3 text-sm text-emerald-800">
                <CheckCircle2 className="h-4 w-4 shrink-0" /> Run {exec.status}{exec.outcome ? ` — ${exec.outcome}` : ""}
              </div>
            ) : (
              <div className="mt-3 rounded-lg border border-dashed px-4 py-8 text-center text-sm text-slate-400">
                No approvals waiting. The human-in-the-loop queue lands here.
              </div>
            )}
          </Card>

          {/* Connectors */}
          <Card className="animate-fade-up">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-slate-900">Connectors</h2>
              <Link href="/docs#connectors" className="text-xs font-medium text-indigo-600 hover:underline">Set up →</Link>
            </div>
            <div className="mt-3 space-y-2">
              {CONNECTORS.map((c) => {
                const Icon = c.icon;
                return (
                  <div key={c.name} className="flex items-center gap-3 rounded-lg border p-2.5 transition hover:bg-slate-50">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-slate-100 text-slate-500"><Icon className="h-4 w-4" /></span>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-slate-800">{c.name}</div>
                      <div className="truncate text-xs text-slate-400">{c.note}</div>
                    </div>
                    <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">Available</span>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Continuity */}
          <div className="animate-fade-up rounded-xl border border-indigo-100 bg-indigo-50/60 p-5">
            <h2 className="flex items-center gap-2 font-semibold text-slate-900"><Users className="h-4 w-4 text-indigo-600" /> Continuity</h2>
            <p className="mt-1.5 text-sm text-slate-600">
              When someone leaves, their judgment stays. Engram captures their decisions as skills before they go.
            </p>
            <Link href="/docs#continuity" className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:underline">
              <BookOpen className="h-4 w-4" /> How knowledge transfer works
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
