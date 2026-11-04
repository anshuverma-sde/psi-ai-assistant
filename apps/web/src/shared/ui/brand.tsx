import { Sparkles } from "lucide-react";
import Link from "next/link";

import { cn } from "@/shared/lib/format";

/** Logo. `inverse` is for use on the brand gradient; `compact` shows only the mark. */
export function BrandMark({ href = "/", inverse = false, compact = false }: {
  href?: string; inverse?: boolean; compact?: boolean;
}) {
  return (
    <Link href={href} aria-label={compact ? "Ask PSI" : undefined}
      className={cn("inline-flex items-center gap-2.5 text-[17px] font-semibold tracking-tight",
        inverse ? "text-primary-fg" : "text-fg")}>
      <span className={cn("grid size-8 shrink-0 place-items-center rounded-lg shadow-sm",
        inverse ? "bg-primary-fg/15 text-primary-fg ring-1 ring-primary-fg/25" : "bg-brand-gradient text-primary-fg")}>
        <Sparkles className="size-4" aria-hidden />
      </span>
      {!compact && "Ask PSI"}
    </Link>
  );
}
