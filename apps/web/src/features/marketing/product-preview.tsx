"use client";

import { Check, FileText, X } from "lucide-react";

import { cn } from "@/shared/lib/format";
import { Avatar, Badge, Stagger, StaggerItem } from "@/shared/ui";

const CHECKS = [
  { ok: true, text: "Second year or above", fact: "year 2" },
  { ok: true, text: "GPA at least 3.5", fact: "gpa 3.7" },
  { ok: false, text: "No Need-Based Grant", fact: "holds grant" },
];

/** Static mock of a real answer — used on marketing and auth screens. */
export function ProductPreview({ className }: { className?: string }) {
  return (
    <Stagger gap={0.12} delay={0.2} className={cn("w-full max-w-md space-y-3", className)}>
      <StaggerItem className="ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-surface-muted px-4 py-2.5 text-sm text-fg">
        I&apos;m a second-year student with a 3.7 GPA and a need-based grant. Can I get the merit scholarship?
      </StaggerItem>

      <StaggerItem className="rounded-2xl border border-border bg-surface p-4 shadow-lg">
        <div className="flex items-center gap-2.5">
          <Avatar name="Northbridge" size="sm" />
          <p className="text-sm font-semibold text-fg">Northbridge University</p>
          <Badge tone="danger" className="ml-auto">Not eligible</Badge>
        </div>
        <p className="mt-3 text-sm leading-relaxed text-fg">
          Not this year. You meet the year and GPA requirements, but the Merit Scholarship can&apos;t be held together with a
          Need-Based Grant <span className="rounded bg-primary-soft px-1 text-[11px] font-semibold text-primary-ink">1</span>.
        </p>
        <ul className="mt-3 space-y-1.5 rounded-xl bg-surface-muted p-3">
          {CHECKS.map((c) => (
            <li key={c.text} className="flex items-center gap-2 text-[13px]">
              {c.ok ? <Check className="size-3.5 text-success" /> : <X className="size-3.5 text-danger" />}
              <span className="text-fg">{c.text}</span>
              <span className="ml-auto text-subtle">{c.fact}</span>
            </li>
          ))}
        </ul>
        <div className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-border px-2.5 py-1 text-xs text-muted">
          <FileText className="size-3.5" /> Scholarship_Rules.pdf · p.4
        </div>
      </StaggerItem>
    </Stagger>
  );
}
