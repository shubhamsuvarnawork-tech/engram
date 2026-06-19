"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, type Skill } from "@/lib/api";
import { Card, Badge, ConfidenceBar } from "@/components/ui";
import { Database, GitBranch, Zap, ShieldAlert } from "lucide-react";

const ICON: Record<string, any> = { data_fetch: Database, decision: GitBranch, action: Zap };

export default function SkillView() {
  const { id } = useParams<{ id: string }>();
  const [skill, setSkill] = useState<Skill | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { api.getSkill(id).then(setSkill).catch((e) => setErr(e.message)); }, [id]);
  if (err) return <p className="text-rose-600">Error: {err}</p>;
  if (!skill) return <p className="text-slate-500">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="font-mono text-xl font-semibold">{skill.name}</h1>
          <Badge tone="indigo">v{skill.version}</Badge>
        </div>
        <p className="mt-1 text-slate-600">{skill.description}</p>
        <div className="mt-3 flex items-center gap-6 text-sm">
          <span className="text-slate-500">Confidence</span><ConfidenceBar value={skill.confidence} />
          <span className="text-slate-500">Freshness</span><ConfidenceBar value={skill.freshness} />
        </div>
        <div className="mt-2 text-sm text-slate-600">
          Inputs: {skill.inputs.map((i) => <code key={i.name} className="mx-1 rounded bg-slate-100 px-1">{i.name}</code>)}
        </div>
      </div>

      <div className="space-y-2">
        <h2 className="font-medium">Compiled workflow</h2>
        {skill.steps.map((s, i) => {
          const Icon = ICON[s.type] || Zap;
          return (
            <Card key={s.id} className="flex items-center gap-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold">{i + 1}</div>
              <Icon className="h-4 w-4 text-indigo-600" />
              <div className="flex-1">
                <div className="font-medium">{s.title}</div>
                <div className="text-xs text-slate-500">
                  {s.tool && <>tool <code>{s.tool}</code> </>}
                  {s.produces && <>→ produces <code>{s.produces}</code></>}
                  {s.type === "decision" && <>consumes {s.consumes?.map((c) => <code key={c} className="mx-0.5">{c}</code>)}</>}
                </div>
              </div>
              <Badge tone="slate">{s.type}</Badge>
              {s.requires_approval && <Badge tone="amber">approval</Badge>}
            </Card>
          );
        })}
      </div>

      {skill.guards.length > 0 && (
        <div className="space-y-2">
          <h2 className="flex items-center gap-2 font-medium"><ShieldAlert className="h-4 w-4 text-amber-600" /> Guards</h2>
          {skill.guards.map((g) => (
            <Card key={g.id} className="border-amber-200 bg-amber-50">
              <div className="text-sm">{g.description}</div>
              <div className="mt-1 text-xs text-slate-500">gates action <code>{g.action}</code> · requires human approval</div>
            </Card>
          ))}
        </div>
      )}

      <Card className="bg-slate-50">
        <h2 className="text-sm font-medium">Provenance</h2>
        <p className="mt-1 text-xs text-slate-500">
          Compiled from {skill.provenance.node_ids.length} knowledge nodes · sources:{" "}
          {skill.provenance.sources.map((s) => <code key={s} className="mx-1">{s}</code>)}
        </p>
      </Card>
    </div>
  );
}
