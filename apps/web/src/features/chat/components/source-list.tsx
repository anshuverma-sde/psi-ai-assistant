"use client";

import { useState } from "react";

import type { Source } from "@/shared/api/types";
import { cn } from "@/shared/lib/format";
import { AnimatePresence, motion } from "@/shared/ui";

/** Numbered source pills; clicking one reveals the quoted passage. */
export function SourceList({ sources, messageId }: { sources: Source[]; messageId: string }) {
  const [open, setOpen] = useState<string | null>(null);
  if (sources.length === 0) return null;
  const active = sources.find((s) => s.id === open);

  return (
    <div className="mt-4 space-y-2.5 border-t border-border pt-4">
      <div className="flex flex-wrap gap-1.5">
        {sources.map((s, i) => (
          <button
            key={s.id}
            id={`cite-${messageId}-${s.id}`}
            onClick={() => setOpen(open === s.id ? null : s.id)}
            aria-expanded={open === s.id}
            className={cn(
              "inline-flex scroll-mt-4 items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-[13px] transition-colors",
              open === s.id ? "border-primary-muted bg-primary-soft text-fg" : "border-border text-muted hover:border-border-strong hover:text-fg",
            )}
          >
            <span className="font-medium text-primary-ink">{i + 1}</span>
            {s.document.replace(/\.pdf$/i, "").replace(/_/g, " ")}
            <span className="text-subtle">p.{s.page}</span>
          </button>
        ))}
      </div>
      <AnimatePresence initial={false}>
        {active && (
          <motion.blockquote
            key={active.id}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden rounded-r-lg border-l-2 border-primary-ink bg-primary-soft/60 pl-3.5 pr-3 text-[13px] leading-relaxed text-muted"
          >
            <p className="py-1">{active.snippet}</p>
            <p className="pb-1 text-subtle">{active.document} — Page {active.page}</p>
          </motion.blockquote>
        )}
      </AnimatePresence>
    </div>
  );
}
