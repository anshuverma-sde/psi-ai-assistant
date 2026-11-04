"use client";

import { Check, ChevronDown, HelpCircle, X } from "lucide-react";
import { useState } from "react";

import type { ConditionTrace, DecisionResult, Source, Verdict } from "@/shared/api/types";
import { cn, humanize } from "@/shared/lib/format";
import { AnimatePresence, Badge, motion, type Tone } from "@/shared/ui";

const VERDICT: Record<Verdict["outcome"], { tone: Tone; label: string }> = {
  ELIGIBLE: { tone: "success", label: "Eligible" },
  NOT_ELIGIBLE: { tone: "danger", label: "Not eligible" },
  NEEDS_INFO: { tone: "primary", label: "Need more details" },
  INFORMATIONAL: { tone: "neutral", label: "Evaluated" },
};
const KIND = { boolean: "Yes / no", choice: "Choice", score: "Score" } as const;

function ResultIcon({ result }: { result: ConditionTrace["result"] }) {
  if (result === "TRUE") return <Check className="mt-0.5 size-3.5 shrink-0 text-success" aria-label="met" />;
  if (result === "FALSE") return <X className="mt-0.5 size-3.5 shrink-0 text-danger" aria-label="not met" />;
  return <HelpCircle className="mt-0.5 size-3.5 shrink-0 text-warning" aria-label="unknown" />;
}

/** "has_need_based_grant" + false → "has need based grant: no" (states the fact, not the rule). */
function factValue(fact: string, value: unknown): string {
  const shown = value === null || value === undefined ? "not provided"
    : typeof value === "boolean" ? (value ? "yes" : "no")
    : Array.isArray(value) ? value.join(", ") : String(value);
  return `${humanize(fact).toLowerCase()}: ${shown}`;
}

function Decision({ decision, sourceIndex }: { decision: DecisionResult; sourceIndex: Map<string, number> }) {
  const outcome = decision.score != null ? `${humanize(decision.outcome.toLowerCase())} · ${decision.score.toFixed(2)}` : decision.outcome;
  const label = { TRUE: "Met", FALSE: "Not met", UNKNOWN: "Unknown" }[outcome] ?? outcome;
  const tone: Tone = decision.passed === true ? "success" : decision.passed === false ? "danger" : "warning";
  return (
    <li className="space-y-2 py-3 first:pt-0 last:pb-0">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-wide text-subtle">{KIND[decision.kind]}</p>
          <p className="text-sm font-medium text-fg">{decision.question}</p>
        </div>
        <Badge tone={tone}>{label}</Badge>
      </div>
      <ul className="space-y-1">
        {decision.trace.map((t) => (
          <li key={`${t.group ?? ""}${t.condition_id}`} className="flex items-start gap-2 text-[13px] text-muted">
            <ResultIcon result={t.result} />
            <span className="min-w-0">
              {t.group && <span className="text-fg">{t.group}: </span>}
              {t.label}
              <span className="text-subtle"> · {factValue(t.fact, t.actual)}</span>
              {sourceIndex.has(t.source_id) && <span className="text-primary-ink"> [{sourceIndex.get(t.source_id)}]</span>}
            </span>
          </li>
        ))}
      </ul>
    </li>
  );
}

/** "How this was decided" — the structured rule checks, not model chain-of-thought. */
export function DecisionTrace({ verdict, decisions, sources }: { verdict: Verdict; decisions: DecisionResult[]; sources: Source[] }) {
  const [open, setOpen] = useState(verdict.outcome !== "INFORMATIONAL");
  const v = VERDICT[verdict.outcome];
  const sourceIndex = new Map(sources.map((s, i) => [s.id, i + 1]));

  return (
    <div className="mt-4 overflow-hidden rounded-xl border border-border bg-surface-muted/50">
      <button onClick={() => setOpen(!open)} aria-expanded={open}
        className="flex w-full items-center gap-2.5 px-4 py-3 text-left">
        <Badge tone={v.tone}>{v.label}</Badge>
        <span className="flex-1 text-[13px] text-muted">How this was decided · {decisions.length} {decisions.length === 1 ? "check" : "checks"}</span>
        <ChevronDown className={cn("size-3.5 text-subtle transition-transform", open && "rotate-180")} />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden">
            <ul className="divide-y divide-border border-t border-border bg-surface px-4 py-3">
              {decisions.map((d) => <Decision key={d.id} decision={d} sourceIndex={sourceIndex} />)}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
