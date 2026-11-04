"use client";

import { CircleHelp, MessageSquare, MessagesSquare, SearchX, ShieldAlert } from "lucide-react";

import { useApiQuery } from "@/shared/api/hooks";
import type { UsageOut } from "@/shared/api/types";
import { formatDate, humanize } from "@/shared/lib/format";
import { Alert, Badge, Card, CardHeader, EmptyState, Skeleton, Stagger, StaggerItem, StatCard, type Tone } from "@/shared/ui";
import { usageApi, usageKey } from "../api";

const STATUS: Record<string, { tone: Tone; label: string }> = {
  answered: { tone: "success", label: "Answered" },
  needs_info: { tone: "primary", label: "Asked for details" },
  no_answer: { tone: "warning", label: "Not in documents" },
  needs_review: { tone: "danger", label: "Needs review" },
};

function useUsage() {
  return useApiQuery(usageKey, usageApi.get, { refetchInterval: 15_000 });
}

function Tiles({ usage }: { usage: UsageOut }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard label="Questions" value={usage.total_questions} icon={<MessagesSquare />}
        hint={usage.avg_latency_ms ? `${(usage.avg_latency_ms / 1000).toFixed(1)}s average` : "No questions yet"} />
      <StatCard label="Answered" value={usage.answered + usage.needs_info} icon={<MessageSquare />} tone="success"
        hint={usage.needs_info ? `${usage.needs_info} asked for details` : "With sources"} />
      <StatCard label="Not in documents" value={usage.no_answer} icon={<SearchX />} tone="warning" hint="Gaps in your files" />
      <StatCard label="Needs review" value={usage.needs_review} icon={<ShieldAlert />} tone="danger" hint="Partial answers" />
    </div>
  );
}

/** KPI row for the overview page. */
export function UsageSummary() {
  const { data, isLoading, error } = useUsage();
  if (isLoading) return <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-32" />)}</div>;
  if (error || !data) return <Alert>{error?.message ?? "Couldn't load usage."}</Alert>;
  return <Tiles usage={data} />;
}

export function UsageStats() {
  const { data, isLoading, error } = useUsage();
  if (isLoading) return <Skeleton className="h-96 w-full" />;
  if (error || !data) return <Alert>{error?.message ?? "Couldn't load usage."}</Alert>;

  const types = Object.entries(data.by_question_type).sort((a, b) => b[1] - a[1]);
  const maxCount = Math.max(1, ...types.map(([, c]) => c));
  return (
    <Stagger gap={0.06} className="space-y-6">
      <StaggerItem><Tiles usage={data} /></StaggerItem>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <StaggerItem>
          <Card className="h-full">
            <CardHeader title="Question types" description="Classified before answering." />
            {types.length === 0 ? (
              <EmptyState icon={<CircleHelp />} title="Nothing yet" />
            ) : (
              <ul className="space-y-4 p-6">
                {types.map(([label, count]) => (
                  <li key={label} className="space-y-1.5">
                    <div className="flex justify-between text-sm">
                      <span className="text-fg">{humanize(label)}</span>
                      <span className="tabular-nums text-muted">{count}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-surface-muted">
                      <div className="h-full rounded-full bg-primary-ink" style={{ width: `${(count / maxCount) * 100}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </StaggerItem>

        <StaggerItem>
          <Card className="h-full">
            <CardHeader title="Recent questions" />
            {data.recent.length === 0 ? (
              <EmptyState icon={<MessageSquare />} title="No questions yet" description="Questions from your visitors will show up here." />
            ) : (
              <ul className="mt-4 divide-y divide-border border-t border-border">
                {data.recent.map((q) => {
                  const s = STATUS[q.status] ?? { tone: "neutral" as Tone, label: humanize(q.status) };
                  return (
                    <li key={q.created_at + q.question} className="flex flex-col gap-2 px-6 py-4 sm:flex-row sm:items-center sm:gap-6">
                      <p className="min-w-0 flex-1 text-[15px] text-fg">{q.question}</p>
                      <div className="flex shrink-0 items-center gap-3">
                        <Badge tone={s.tone}>{s.label}</Badge>
                        <span className="text-[13px] tabular-nums text-subtle">{formatDate(q.created_at)}</span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </Card>
        </StaggerItem>
      </div>
    </Stagger>
  );
}
