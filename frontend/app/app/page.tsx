"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api, SAMPLE_REFUND_DOC, type SkillSummary, type Execution } from "@/lib/api";
import {
  Sparkles, Loader2, ArrowUpRight, Network, Workflow, ShieldCheck, Activity,
  Hand, CheckCircle2, AlertTriangle, Mail, MessageSquare, GitBranch, Database,
  Users, FileText,
} from "lucide-react";

const CONNECTORS = [
  { name: "Mail", icon: Mail, note: "Approvals & commitments" },
  { name: "Slack", icon: MessageSquare, note: "Decisions in threads" },
  { name: "Jira", icon: GitBranch, note: "Triage & routing" },
  { name: "CRM", icon: Database, note: "Account context" },
];

const STAGES = [
  { label: "Ingest policy", sub: "extract knowledge nodes" },
  { label: "Compile skill", sub: "graph to workflow" },
  { label: "Execute", sub: "run on a live account" },
  { label: "Human decision", sub: "approve or override" },
];

const NODES = [
  { x: 70, y: 168, r: 7, c: "#22d3ee", l: "policy" },
  { x: 150, y: 92, r: 5, c: "#a78bfa", l: "refund" },
  { x: 150, y: 246, r: 5, c: "#818cf8", l: "fraud" },
  { x: 242, y: 64, r: 4, c: "#22d3ee", l: "auto-approve" },
  { x: 254, y: 152, r: 6, c: "#a78bfa", l: "manual review" },
  { x: 244, y: 252, r: 4, c: "#818cf8", l: "escalate" },
  { x: 340, y: 110, r: 5, c: "#22d3ee", l: "Finance" },
  { x: 346, y: 206, r: 4, c: "#a78bfa", l: "$5k+" },
  { x: 430, y: 152, r: 7, c: "#818cf8", l: "decision" },
  { x: 98, y: 96, r: 3, c: "#818cf8", l: "" },
  { x: 306, y: 286, r: 3, c: "#22d3ee", l: "" },
  { x: 414, y: 76, r: 3, c: "#a78bfa", l: "" },
];
const EDGES: [number, number][] = [
  [0,1],[0,2],[0,9],[1,3],[1,4],[2,4],[2,5],[4,6],[4,7],[5,7],[3,6],[6,8],[7,8],[5,10],[8,11],[3,11],
];

function BrainGraph() {
  return (
    <svg viewBox="0 0 480 320" className="h-full w-full" aria-hidden="true">
      <defs>
        <filter id="egGlowF" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="3.2" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
      <g stroke="#6366f1" strokeWidth="1" opacity="0.4">
        {EDGES.map(([a, b], i) => (
          <line key={i} className="eg-edge" x1={NODES[a].x} y1={NODES[a].y} x2={NODES[b].x} y2={NODES[b].y} style={{ animationDelay: `${i * 0.15}s` }} />
        ))}
      </g>
      <g filter="url(#egGlowF)">
        {NODES.map((n, i) => (
          <circle key={i} className="eg-node" cx={n.x} cy={n.y} r={n.r} fill={n.c} style={{ animationDelay: `${i * 0.27}s` }} />
        ))}
      </g>
      <g className="font-jb" fill="#cbd5e1" fontSize="9" opacity="0.7">
        {NODES.map((n, i) => (n.l ? (
          <text key={i} x={n.x > 360 ? n.x - 8 : n.x + 10} y={n.y - 9} textAnchor={n.x > 360 ? "end" : "start"}>{n.l}</text>
        ) : null))}
      </g>
    </svg>
  );
}

function useCountUp(target: number, ms = 850) {
  const [n, setN] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const from = n;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / ms);
      setN(Math.round(from + (target - from) * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]); // eslint-disable-line react-hooks/exhaustive-deps
  return n;
}

const TONES: Record<string, string> = {
  indigo: "bg-indigo-500/15 text-indigo-300 ring-indigo-400/25",
  violet: "bg-violet-500/15 text-violet-300 ring-violet-400/25",
  cyan: "bg-cyan-500/15 text-cyan-300 ring-cyan-400/25",
  amber: "bg-amber-500/15 text-amber-300 ring-amber-400/25",
  slate: "bg-white/5 text-slate-300 ring-white/10",
};

function Stat({ icon: Icon, label, value, suffix = "", hint, tone = "indigo", ready }: {
  icon: any; label: string; value: number; suffix?: string; hint?: string;
  tone?: "indigo" | "violet" | "cyan" | "amber" | "slate"; ready: boolean;
}) {
  const n = useCountUp(value);
  return (
    <div className="animate-fade-up rounded-2xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl">
      <div className="flex items-center gap-2">
        <span className={`grid h-7 w-7 place-items-center rounded-lg ring-1 ${TONES[tone]}`}><Icon className="h-4 w-4" /></span>
        <span className="font-jb text-[11px] uppercase tracking-wider text-slate-500">{label}</span>
      </div>
      <div className="mt-3 font-display text-3xl font-semibold text-white">{ready ? `${n}${suffix}` : "—"}</div>
      {hint && <div className="mt-0.5 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

function Bar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const grad = pct >= 80 ? "from-emerald-400 to-cyan-400" : pct >= 60 ? "from-amber-400 to-orange-400" : "from-rose-400 to-pink-400";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-white/10">
        <div className={`h-full rounded-full bg-gradient-to-r ${grad}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-jb text-xs text-slate-400">{pct}%</span>
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
          <li key={st.label} className={`flex items-center gap-3 rounded-lg px-2 py-1.5 ${isActive ? "bg-white/5" : ""}`}>
            <span className="grid h-7 w-7 shrink-0 place-items-center">
              {done ? <CheckCircle2 className="h-5 w-5 text-cyan-300" />
                : waiting ? <Hand className="h-5 w-5 text-amber-300" />
                : running ? <Loader2 className="h-5 w-5 animate-spin text-indigo-300" />
                : <span className="grid h-6 w-6 place-items-center rounded-full border border-white/15 font-jb text-[11px] text-slate-500">{i + 1}</span>}
            </span>
            <div className="min-w-0 flex-1">
              <div className={`text-sm font-medium ${done ? "text-slate-200" : isActive ? "text-white" : "text-slate-500"}`}>{st.label}</div>
              <div className="text-xs text-slate-500">{st.sub}</div>
            </div>
            {waiting && <span className="font-jb shrink-0 text-[11px] text-amber-300">waiting on you</span>}
          </li>
        );
      })}
    </ol>
  );
}

function Panel({ children, className = "" }: { children: any; className?: string }) {
  return <div className={`animate-fade-up rounded-2xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl ${className}`}>{children}</div>;
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
      setSkills(await api.listSkills(id));
      setActive(2);
      if (skill.id) {
        setStage("Running on a flagged account");
        const e = await api.execute(skill.id, { customer_id: "cust_fraud" });
        setExec(e);
        if (e.status === "pending_approval") { push("Execution paused -> awaiting human approval"); setActive(3); }
        else { push(`Execution ${e.status}${e.outcome ? ` -> ${e.outcome}` : ""}`); setActive(4); }
      } else setActive(4);
      setStage("");
    } catch (e: any) { setErr(e.message); push(`Error: ${e.message}`); setActive(-1); }
    setBusy(false);
  }

  async function decide(decision: string, action?: string) {
    if (!exec?.approval_id) return;
    try {
      const e = await api.decide(exec.approval_id, { decision, action, decided_by: "you@acme.com", reason: "reviewed in dashboard" });
      setExec(e); setActive(4);
      push(decision === "approve" ? "Approved -> agent completed the run" : "Overridden -> correction recorded");
    } catch (e: any) { setErr(e.message); }
  }

  const avgConf = useMemo(() => (skills.length ? Math.round((skills.reduce((s, k) => s + k.confidence, 0) / skills.length) * 100) : 0), [skills]);
  const pending = exec?.status === "pending_approval" ? 1 : 0;
  const initialized = cid !== null;

  return (
    <div className="relative -mt-8 overflow-hidden rounded-[28px] border border-white/10 bg-[#06070f] px-5 py-7 text-slate-200 shadow-2xl shadow-black/50 sm:px-8">
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <div className="absolute -left-32 -top-24 h-80 w-80 rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="absolute right-[-8%] top-10 h-80 w-80 rounded-full bg-violet-600/15 blur-[120px]" />
        <div className="absolute bottom-[-12%] left-1/3 h-80 w-80 rounded-full bg-cyan-500/10 blur-[120px]" />
      </div>

      <div className="relative mx-auto max-w-5xl space-y-6">
        {/* Hero */}
        <div className="grid gap-6 overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl lg:grid-cols-[1.05fr_1fr] lg:p-8">
          <div className="flex flex-col justify-center">
            <div className="font-jb flex items-center gap-2 text-[11px] uppercase tracking-[0.2em] text-cyan-300/80">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyan-400 opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-400" />
              </span>
              live · {initialized ? cid : "engram api"}
            </div>
            <h1 className="mt-4 font-display text-4xl font-bold leading-[1.05] tracking-tight text-white sm:text-5xl">
              Your company<br /><span className="bg-gradient-to-r from-indigo-300 via-violet-300 to-cyan-300 bg-clip-text text-transparent">brain</span>, online.
            </h1>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-slate-400">
              Watch a real policy become a guarded, executable skill — and hand you the decision. One click runs the whole loop, live.
            </p>
            <div className="mt-6">
              <button onClick={runLoop} disabled={busy}
                className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-violet-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-900/40 ring-1 ring-white/15 transition hover:shadow-indigo-700/50 disabled:opacity-60">
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {busy ? `${stage || "Working"}…` : initialized ? "Re-run the brain" : "Run the brain"}
              </button>
            </div>
          </div>
          <div className="relative min-h-[210px]">
            <div className="eg-glow absolute inset-0 bg-[radial-gradient(circle_at_60%_45%,rgba(99,102,241,0.18),transparent_65%)]" />
            <BrainGraph />
          </div>
        </div>

        {err && (
          <div className="flex items-center gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-2.5 text-sm text-rose-200">
            <AlertTriangle className="h-4 w-4 shrink-0" /> {err}
          </div>
        )}

        {/* KPIs */}
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Stat icon={Network} label="Knowledge" value={nodes} hint="nodes ingested" tone="cyan" ready={initialized} />
          <Stat icon={Workflow} label="Skills" value={skills.length} hint="compiled & live" tone="violet" ready={initialized} />
          <Stat icon={ShieldCheck} label="Confidence" value={avgConf} suffix="%" hint="avg across skills" tone="indigo" ready={initialized} />
          <Stat icon={Activity} label="Approvals" value={pending} hint={pending ? "needs review" : "all clear"} tone={pending ? "amber" : "slate"} ready={initialized} />
        </div>

        {/* Main grid */}
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="space-y-5 lg:col-span-2">
            <Panel>
              <div className="flex items-center justify-between">
                <h2 className="font-display font-semibold text-white">Compile pipeline</h2>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${busy ? TONES.amber : initialized ? TONES.cyan : TONES.slate}`}>{busy ? "running" : initialized ? "ready" : "idle"}</span>
              </div>
              <div className="mt-3 rounded-xl border border-white/10 bg-black/20 p-3">
                <Pipeline active={active} awaiting={pending > 0} />
              </div>
              <details className="mt-3 rounded-lg border border-white/10 bg-black/20 p-3">
                <summary className="font-jb flex cursor-pointer items-center gap-2 text-xs text-slate-400"><FileText className="h-3.5 w-3.5" /> source · refund-policy.txt</summary>
                <pre className="mt-2 whitespace-pre-wrap text-xs leading-relaxed text-slate-400">{SAMPLE_REFUND_DOC}</pre>
              </details>
              {log.length > 0 && (
                <details className="mt-3 rounded-lg border border-white/10 bg-black/30 p-3" open>
                  <summary className="font-jb cursor-pointer text-xs text-slate-400">live trace</summary>
                  <pre className="font-jb mt-2 overflow-x-auto rounded-lg bg-black/40 p-3 text-xs leading-relaxed text-cyan-100/90">{log.join("\n")}</pre>
                </details>
              )}
            </Panel>

            <Panel>
              <div className="flex items-center justify-between">
                <h2 className="font-display font-semibold text-white">Skills library</h2>
                {skills.length > 0 && <span className="font-jb text-xs text-slate-500">{skills.length} compiled</span>}
              </div>
              {skills.length > 0 ? (
                <div className="mt-3 space-y-2.5">
                  {skills.map((s) => {
                    const live = s.confidence >= 0.8;
                    return (
                      <Link key={s.id} href={`/skills/${s.id}`} className="group flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.02] p-3 transition hover:border-indigo-400/30 hover:bg-white/[0.04]">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-indigo-500/15 text-indigo-300 ring-1 ring-indigo-400/25"><Workflow className="h-4 w-4" /></span>
                            <span className="font-jb text-sm text-white">{s.name}</span>
                            <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ${live ? TONES.cyan : TONES.amber}`}>{live ? "live" : "review"}</span>
                          </div>
                          <div className="mt-2"><Bar value={s.confidence} /></div>
                        </div>
                        <ArrowUpRight className="h-4 w-4 shrink-0 text-slate-500 transition group-hover:text-indigo-300" />
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <div className="mt-3 rounded-xl border border-dashed border-white/10 px-4 py-8 text-center text-sm text-slate-500">No skills yet. Run the brain to compile your first.</div>
              )}
            </Panel>
          </div>

          <div className="space-y-5">
            <Panel className={pending ? "ring-1 ring-amber-400/20" : ""}>
              <div className="flex items-center justify-between">
                <h2 className="flex items-center gap-2 font-display font-semibold text-white"><Hand className="h-4 w-4 text-amber-300" /> Approvals</h2>
                {pending > 0 && <span className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${TONES.amber}`}>{pending} waiting</span>}
              </div>
              {exec?.status === "pending_approval" && exec.pending ? (
                <div className="mt-3 rounded-xl border border-amber-400/20 bg-amber-500/10 p-3">
                  <span className="font-jb rounded bg-black/30 px-1.5 py-0.5 text-[11px] text-amber-200/90">account · cust_fraud</span>
                  <div className="mt-2 text-sm text-slate-200">Agent wants to <strong className="font-semibold text-white">{exec.pending.action}</strong></div>
                  <p className="mt-1 text-xs text-slate-400">{exec.pending.reason}</p>
                  {exec.pending.triggered_guards.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {exec.pending.triggered_guards.map((g) => <span key={g} className="font-jb rounded-full bg-amber-500/15 px-2 py-0.5 text-[11px] text-amber-200 ring-1 ring-amber-400/20">{g}</span>)}
                    </div>
                  )}
                  <div className="mt-3 flex gap-2">
                    <button onClick={() => decide("approve")} className="flex-1 rounded-lg bg-gradient-to-r from-indigo-500 to-violet-500 px-3 py-1.5 text-sm font-semibold text-white ring-1 ring-white/15 transition hover:brightness-110">Approve</button>
                    <button onClick={() => decide("override", "deny_refund")} className="flex-1 rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-sm text-slate-200 transition hover:bg-white/10">Override</button>
                  </div>
                </div>
              ) : exec ? (
                <div className="mt-3 flex items-center gap-2 rounded-xl border border-emerald-400/20 bg-emerald-500/10 px-3 py-3 text-sm text-emerald-200"><CheckCircle2 className="h-4 w-4 shrink-0" /> Run {exec.status}{exec.outcome ? ` — ${exec.outcome}` : ""}</div>
              ) : (
                <div className="mt-3 rounded-xl border border-dashed border-white/10 px-4 py-8 text-center text-sm text-slate-500">No approvals waiting. The HITL queue lands here.</div>
              )}
            </Panel>

            <Panel>
              <div className="flex items-center justify-between">
                <h2 className="font-display font-semibold text-white">Connectors</h2>
                <Link href="/docs#connectors" className="font-jb text-xs text-indigo-300 hover:text-indigo-200">set up ↗</Link>
              </div>
              <div className="mt-3 space-y-2">
                {CONNECTORS.map((c) => {
                  const Icon = c.icon;
                  return (
                    <div key={c.name} className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.02] p-2.5">
                      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white/5 text-slate-300 ring-1 ring-white/10"><Icon className="h-4 w-4" /></span>
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium text-slate-200">{c.name}</div>
                        <div className="truncate text-xs text-slate-500">{c.note}</div>
                      </div>
                      <span className="font-jb shrink-0 rounded-full bg-white/5 px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-400 ring-1 ring-white/10">soon</span>
                    </div>
                  );
                })}
              </div>
            </Panel>

            <div className="animate-fade-up overflow-hidden rounded-2xl border border-indigo-400/20 bg-gradient-to-br from-indigo-500/10 to-violet-500/5 p-5">
              <h2 className="flex items-center gap-2 font-display font-semibold text-white"><Users className="h-4 w-4 text-indigo-300" /> Continuity</h2>
              <p className="mt-1.5 text-sm text-slate-400">When someone leaves, their judgment stays — captured as skills before they go.</p>
              <Link href="/docs#continuity" className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-indigo-300 hover:text-indigo-200">How knowledge transfer works <ArrowUpRight className="h-4 w-4" /></Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
