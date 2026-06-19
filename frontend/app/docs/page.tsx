import type { ReactNode } from "react";
import Link from "next/link";
import { Card, Badge } from "@/components/ui";
import { EngramMark } from "@/components/logo";
import {
  Network, Workflow, ShieldCheck, Repeat, Plug, FileText,
  Mail, MessageSquare, GitBranch, Database, Users, Lock,
  CheckCircle2, Sparkles, ArrowRight,
} from "lucide-react";

export const metadata = {
  title: "Docs — Engram",
  description:
    "How Engram turns your company's decisions into executable, provenance-linked skills your AI agents run safely, with a human in the loop.",
};

function Section({
  id, eyebrow, title, children,
}: { id?: string; eyebrow?: string; title: string; children: ReactNode }) {
  return (
    <section id={id} className="scroll-mt-24">
      {eyebrow && (
        <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-indigo-600">{eyebrow}</div>
      )}
      <h2 className="text-xl font-semibold tracking-tight text-slate-900">{title}</h2>
      <div className="mt-3 space-y-4 text-[15px] leading-relaxed text-slate-600">{children}</div>
    </section>
  );
}

function Concept({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <Card className="h-full">
      <div className="flex items-center gap-2.5">
        <span className="grid h-9 w-9 place-items-center rounded-lg bg-indigo-50 text-indigo-600">{icon}</span>
        <h3 className="font-medium text-slate-900">{title}</h3>
      </div>
      <p className="mt-2.5 text-sm leading-relaxed text-slate-600">{children}</p>
    </Card>
  );
}

function Log({ lines }: { lines: string[] }) {
  return (
    <pre className="overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs leading-relaxed text-slate-100">
      {lines.join("\n")}
    </pre>
  );
}

export default function Docs() {
  return (
    <div className="space-y-10 pb-12">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-slate-500">
        <Link href="/app" className="hover:text-slate-800">Engram</Link>
        <span className="text-slate-300">/</span>
        <span className="font-medium text-slate-700">Docs</span>
      </nav>

      {/* Hero */}
      <div className="rounded-2xl bg-[#0B1020] px-8 py-10">
        <div className="flex items-center gap-3">
          <EngramMark className="h-9 w-9" />
          <span className="text-2xl font-semibold tracking-tight text-white">Engram Docs</span>
        </div>
        <h1 className="mt-5 max-w-2xl text-3xl font-semibold leading-tight text-white">
          The company brain that turns decisions into safe, runnable skills.
        </h1>
        <p className="mt-3 max-w-2xl text-slate-300">
          Engram learns how your company actually makes decisions, compiles that knowledge into
          executable, provenance-linked skills, and lets your AI agents run them — always with a
          human in the loop.
        </p>
        <div className="mt-6 flex flex-wrap gap-2 text-xs">
          {["Knowledge graph", "Skill compiler", "Human-in-the-loop", "Full provenance"].map((t) => (
            <span key={t} className="rounded-full bg-white/10 px-3 py-1 text-slate-200">{t}</span>
          ))}
        </div>
      </div>

      {/* On this page */}
      <Card>
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">On this page</div>
        <div className="mt-2 grid gap-x-6 gap-y-1.5 text-sm text-indigo-600 sm:grid-cols-2">
          <a href="#what" className="hover:underline">1. What is Engram?</a>
          <a href="#concepts" className="hover:underline">2. Key concepts</a>
          <a href="#pipeline" className="hover:underline">3. How it works, end to end</a>
          <a href="#example" className="hover:underline">4. Worked example: refunds</a>
          <a href="#connectors" className="hover:underline">5. Connectors</a>
          <a href="#continuity" className="hover:underline">6. Continuity (knowledge transfer)</a>
          <a href="#email" className="hover:underline">7. Example: email reply with approval</a>
          <a href="#safety" className="hover:underline">8. Safety model</a>
        </div>
      </Card>

      <Section id="what" eyebrow="Overview" title="What is Engram?">
        <p>
          Most of a company's real intelligence — why refunds over $200 need a manager, which
          customers never get auto-cancelled, how deals get discounted — lives in people's heads,
          buried Slack threads, and scattered docs. When someone leaves, it walks out the door.
          And today's AI agents can't act on it, because they have no reliable, structured access to
          how your company actually decides things.
        </p>
        <p>
          <strong className="font-medium text-slate-800">Engram is the company brain.</strong> It
          ingests your decisions and policies, builds a living knowledge graph of how work really
          happens, and <strong className="font-medium text-slate-800">compiles that graph into
          skills</strong> — concrete, step-by-step workflows an agent can execute. Every skill traces
          back to the source that justified it, and every consequential action pauses for human
          approval before it runs.
        </p>
      </Section>

      <Section id="concepts" eyebrow="Building blocks" title="Key concepts">
        <div className="grid gap-4 sm:grid-cols-2">
          <Concept icon={<Network className="h-5 w-5" />} title="Knowledge graph">
            A structured map of your company's policies, decisions, entities, and the rules that
            connect them — built from what you ingest, not from guesswork.
          </Concept>
          <Concept icon={<Workflow className="h-5 w-5" />} title="Skill">
            A compiled, runnable workflow generated deterministically from the graph: ordered steps,
            inputs, guardrails, and approval points. This is the moat — knowledge made executable.
          </Concept>
          <Concept icon={<ShieldCheck className="h-5 w-5" />} title="Human-in-the-loop (HITL)">
            Before any consequential step runs, the agent pauses and surfaces exactly what it is about
            to do. A human approves or overrides. Nothing irreversible happens unattended.
          </Concept>
          <Concept icon={<Repeat className="h-5 w-5" />} title="Learning loop">
            Every approval and override is captured and fed back into the graph, nudging skill
            confidence up or down so Engram tracks how your company really decides over time.
          </Concept>
          <Concept icon={<FileText className="h-5 w-5" />} title="Provenance">
            Every node, rule, and skill links back to the exact source that justified it — so you can
            always answer "why did the agent do that?" with a citation, not a shrug.
          </Concept>
          <Concept icon={<Plug className="h-5 w-5" />} title="Connectors">
            Engram plugs into the tools where decisions live — Mail, Slack, Jira, and CRM — so the
            brain stays current as your company works.
          </Concept>
        </div>
      </Section>

      <Section id="pipeline" eyebrow="The pipeline" title="How it works, end to end">
        <p>Engram runs the same five-stage loop whether you are encoding one policy or a whole department:</p>
        <ol className="space-y-3">
          {([
            ["Ingest", "Feed Engram a policy, a decision thread, or a connected source. It extracts the entities and rules into knowledge nodes."],
            ["Build the graph", "Nodes are linked into the knowledge graph with their relationships and provenance back to the source."],
            ["Generate a skill", "The Skill Generation Engine deterministically compiles the relevant slice of the graph into a runnable, step-by-step workflow with a confidence score."],
            ["Execute with approval", "An agent runs the skill. At each consequential step it pauses for human approval, showing what it will do and why."],
            ["Learn", "Approvals and overrides are recorded and fed back, adjusting confidence and improving the next run."],
          ] as [string, string][]).map(([t, d], i) => (
            <li key={t} className="flex gap-3">
              <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-indigo-600 text-xs font-semibold text-white">{i + 1}</span>
              <span><strong className="font-medium text-slate-800">{t}.</strong> {d}</span>
            </li>
          ))}
        </ol>
      </Section>

      <Section id="example" eyebrow="Worked example" title="A refund policy becomes a skill">
        <p>
          This is the exact flow behind the{" "}
          <Link href="/app" className="font-medium text-indigo-600 hover:underline">Ingest + Generate</Link>{" "}
          button on your dashboard. Start with a plain-English policy:
        </p>
        <Card className="bg-slate-50">
          <div className="mb-2 flex items-center gap-2 text-xs text-slate-500">
            <FileText className="h-4 w-4" /> refund-policy.txt
          </div>
          <p className="text-sm leading-relaxed text-slate-700">
            "Customers can request a refund within 30 days of purchase. Refunds under $200 can be
            auto-approved. Refunds of $200 or more require manager approval. Always log the reason and
            notify the customer by email."
          </p>
        </Card>
        <p>Engram ingests it, builds the graph, and compiles a skill:</p>
        <Log lines={[
          "Created tenant co_ced65dec",
          "Ingested policy -> 4 knowledge nodes",
          "Generated skill \"refund_customer\" (confidence 81%)",
        ]} />
        <p>
          The generated{" "}
          <code className="rounded bg-slate-100 px-1.5 py-0.5 text-[13px] text-slate-800">refund_customer</code>{" "}
          skill is a runnable workflow. When an agent executes it, the human-in-the-loop gate looks like this:
        </p>
        <Card>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm text-slate-800">refund_customer</span>
              <Badge tone="amber">awaiting approval</Badge>
            </div>
            <span className="text-xs text-slate-400">step 3 of 4</span>
          </div>
          <p className="mt-3 text-sm text-slate-600">
            Refund request is <strong className="font-medium text-slate-800">$240</strong> (over the
            $200 threshold) — policy requires manager approval. The agent has paused and is requesting
            sign-off before issuing the refund.
          </p>
          <div className="mt-4 flex gap-2">
            <span className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white">Approve</span>
            <span className="rounded-lg border px-3 py-1.5 text-sm text-slate-700">Override</span>
          </div>
        </Card>
        <p>
          Approve, and the agent finishes the run and logs it. Override, and Engram records your
          correction. Both outcomes feed the learning loop and adjust the skill's confidence.
        </p>
      </Section>

      <Section id="connectors" eyebrow="Where decisions live" title="Connectors">
        <p>Engram keeps the brain current by connecting to the tools your team already uses:</p>
        <div className="grid gap-4 sm:grid-cols-2">
          <Concept icon={<Mail className="h-5 w-5" />} title="Mail">
            Learns approval chains and customer commitments from email, and can draft replies for
            one-click approval.
          </Concept>
          <Concept icon={<MessageSquare className="h-5 w-5" />} title="Slack">
            Captures the decisions and rationale that happen in threads before they are ever written down.
          </Concept>
          <Concept icon={<GitBranch className="h-5 w-5" />} title="Jira">
            Understands how work is triaged, prioritized, and routed across your team.
          </Concept>
          <Concept icon={<Database className="h-5 w-5" />} title="CRM">
            Knows account context — tiers, owners, history — so skills make the right call per customer.
          </Concept>
        </div>
      </Section>

      <Section id="continuity" eyebrow="Don't lose what people know" title="Continuity — knowledge that outlives the org chart">
        <p>
          When a teammate leaves, their judgment usually leaves with them. Engram's Continuity
          captures the decisions, exceptions, and "how we actually do this" knowledge as skills while
          people are still here — so offboarding becomes a transfer of a living brain, not a frantic
          handover doc.
        </p>
        <Card className="bg-slate-50">
          <div className="flex items-start gap-2.5">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-indigo-50 text-indigo-600"><Users className="h-5 w-5" /></span>
            <div>
              <div className="text-sm font-medium text-slate-900">Example: a support lead offboards</div>
              <p className="mt-1 text-sm text-slate-600">
                Their refund exceptions, escalation rules, and VIP-account playbook are already
                compiled into skills. The next person — or an agent — picks up exactly where they left
                off, with the reasoning intact and cited.
              </p>
            </div>
          </div>
        </Card>
      </Section>

      <Section id="email" eyebrow="Example" title="Automated email reply, with approval">
        <p>A common first skill. Engram drafts the response from your policies and account context, then waits for you:</p>
        <ol className="space-y-2">
          {[
            "A customer emails asking for a refund outside the 30-day window.",
            "Engram drafts a reply grounded in your refund policy and the customer's CRM tier.",
            "You see the draft with one-click Approve / Edit / Reject — nothing sends on its own.",
            "On approve it sends and logs the decision; on edit, your change trains the next draft.",
          ].map((d, i) => (
            <li key={i} className="flex gap-3">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" />
              <span>{d}</span>
            </li>
          ))}
        </ol>
        <p className="text-sm text-slate-500">The agent never sends on its own — approval is the default, not an afterthought.</p>
      </Section>

      <Section id="safety" eyebrow="By design" title="Safety model">
        <div className="grid gap-4 sm:grid-cols-3">
          <Concept icon={<ShieldCheck className="h-5 w-5" />} title="Approval-first">
            Consequential steps pause for a human. Irreversible actions never run unattended.
          </Concept>
          <Concept icon={<FileText className="h-5 w-5" />} title="Provenance">
            Every action traces to the source that justified it. "Why did it do that?" always has an answer.
          </Concept>
          <Concept icon={<Lock className="h-5 w-5" />} title="Tenant-isolated">
            Each company's brain is its own tenant. Your knowledge and skills stay yours.
          </Concept>
        </div>
      </Section>

      {/* CTA */}
      <div className="rounded-2xl border border-indigo-100 bg-indigo-50/60 px-8 py-8">
        <h2 className="text-lg font-semibold text-slate-900">Try it in 30 seconds</h2>
        <p className="mt-1 max-w-xl text-sm text-slate-600">
          Run the refund example end to end — ingest a policy, compile it into a skill, and watch the
          human-in-the-loop gate in action.
        </p>
        <Link href="/app" className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
          <Sparkles className="h-4 w-4" /> Open the console <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
}
