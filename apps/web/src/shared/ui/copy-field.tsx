"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { cn } from "@/shared/lib/format";
import { AnimatePresence, motion } from "./motion";

export function useCopy(timeout = 1600) {
  const [copied, setCopied] = useState(false);
  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const area = Object.assign(document.createElement("textarea"), { value: text });
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }
    setCopied(true);
    setTimeout(() => setCopied(false), timeout);
  };
  return { copied, copy };
}

/** Read-only value with a copy button (URLs, tokens, embed snippets). */
export function CopyField({ value, label, multiline = false }: { value: string; label: string; multiline?: boolean }) {
  const { copied, copy } = useCopy();
  return (
    <div className="group relative rounded-lg border border-border bg-surface-muted">
      <pre
        aria-label={label}
        className={cn(
          "py-3 pl-3.5 pr-24 font-mono text-[13px] leading-relaxed text-fg",
          multiline ? "whitespace-pre-wrap break-all" : "overflow-x-auto whitespace-nowrap",
        )}
      >
        {value}
      </pre>
      <button
        onClick={() => copy(value)}
        aria-label={`Copy ${label}`}
        className="absolute right-2 top-2 inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 text-[13px] font-medium text-muted shadow-sm transition-colors hover:text-fg"
      >
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={copied ? "done" : "copy"}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.12 }}
            className="inline-flex items-center gap-1"
          >
            {copied ? <Check className="size-3.5 text-success" /> : <Copy className="size-3.5" />}
            {copied ? "Copied" : "Copy"}
          </motion.span>
        </AnimatePresence>
      </button>
    </div>
  );
}
