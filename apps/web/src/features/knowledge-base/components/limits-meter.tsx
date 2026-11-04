import type { KnowledgeBaseLimits } from "@/shared/api/types";
import { Progress } from "@/shared/ui";

export function LimitsMeter({ limits }: { limits: KnowledgeBaseLimits }) {
  const full = limits.remaining_documents === 0;
  return (
    <div className="space-y-3">
      <div className="flex items-baseline justify-between text-sm">
        <span className="text-fg">
          <span className="font-medium tabular-nums">{limits.used_documents}</span>
          <span className="text-subtle"> / {limits.max_documents} documents</span>
        </span>
        {full && <span className="text-[13px] font-medium text-warning">Limit reached</span>}
      </div>
      <Progress value={limits.used_documents} max={limits.max_documents} tone={full ? "warning" : "primary"} />
      <p className="text-[13px] text-subtle">PDF only · up to {limits.max_file_mb} MB and {limits.max_pages} pages each</p>
    </div>
  );
}
