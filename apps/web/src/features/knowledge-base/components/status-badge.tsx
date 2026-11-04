import type { DocumentOut } from "@/shared/api/types";
import { StatusDot, type Tone } from "@/shared/ui";

const STATUS: Record<DocumentOut["status"], { tone: Tone; label: string; pulse?: boolean }> = {
  READY: { tone: "success", label: "Ready" },
  PROCESSING: { tone: "primary", label: "Processing", pulse: true },
  PENDING: { tone: "neutral", label: "Queued", pulse: true },
  FAILED: { tone: "danger", label: "Failed" },
};

export function StatusBadge({ status }: { status: DocumentOut["status"] }) {
  const s = STATUS[status];
  return <StatusDot tone={s.tone} pulse={s.pulse}>{s.label}</StatusDot>;
}
