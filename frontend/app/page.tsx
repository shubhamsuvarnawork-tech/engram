"use client";
import { useState } from "react";
import Link from "next/link";
import { api, SAMPLE_REFUND_DOC, type SkillSummary } from "@/lib/api";
import { Card, Button, Badge, ConfidenceBar } from "@/components/ui";
import { EngramMark } from "@/components/logo";
import { Sparkles, ArrowRight } from "lucide-react";

export default function Dashboard() {
  const [, setCid] = useState<string | null>(null);
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState<string[]>([]);

  const push = (m: string) => setLog((l) => [...l, m]);

  async function bootstrapDemo() {
    setBusy(true); setLog([]);
    try {
      const { id } = await api.createCompany("Acme");
      setCid(id); push(`Created tenant ${id}`);
      const ing = await api.ingest(id, SAMPLE_REFUND_DOC);
      push(`Ingested policy -> ${ing.nodes_created.length} knowledge nodes`);
      const skill = await api.generate(id, "refund_customer");
      push(`Generated skill "${skill.name}" (confidence ${(skill.confidence * 100).toFixed(0)}%)`);
      setSkills(await api.listSkills(id));
    } catch (e: any) { push(`Error: ${e.message}`); }
    setBusy(false);
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-[#0B1020] px-8 py-10">
        <div className="flex items-center gap-3">
          <EngramMark className="h-9 w-9" />
          <span className="text-3xl font-semibold tracking-tight text-white">Engram</span>
        </div>
        <p className="mt-1 text-sm text-indigo-300">organizational memory, made executable</p>
        <h1 className="mt-6 text-2xl font-semibold text-white">Organizational intelligence, compiled.</h1>
        <p className="mt-2 max-w-2xl text-slate-300">
          Engram ingests how your company actually makes decisions and compiles that
          knowledge into executable, provenance-linked skills your agents can run safely.
        </p>
      </div>

      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-medium">Try the vertical slice</h2>
            <p className="text-sm text-slate-500">
              Ingest a sample refund policy, then compile it into a runnable skill.
            </p>
          </div>
          <Button onClick={bootstrapDemo} disabled={busy}>
            <span className="inline-flex items-center gap-1.5"><Sparkles className="h-4 w-4" />
              {busy ? "Working..." : "Ingest + Generate"}</span>
          </Button>
        </div>
        {log.length > 0 && (
          <pre className="mt-4 rounded-lg bg-slate-900 p-3 text-xs text-slate-100">{log.join("\n")}</pre>
        )}
      </Card>

      {skills.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-medium">Generated skills</h2>
          {skills.map((s) => (
            <Card key={s.id} className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm">{s.name}</span>
                  <Badge tone="indigo">goal: {s.goal}</Badge>
                </div>
                <div className="mt-2"><ConfidenceBar value={s.confidence} /></div>
              </div>
              <Link href={`/skills/${s.id}`} className="text-sm font-medium text-indigo-600 hover:underline">
                <span className="inline-flex items-center gap-1">View workflow <ArrowRight className="h-4 w-4" /></span>
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
