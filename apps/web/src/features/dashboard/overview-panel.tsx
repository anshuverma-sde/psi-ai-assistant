"use client";

import { ArrowRight, Bot, Check, FileText } from "lucide-react";
import Link from "next/link";

import { assistantApi, assistantKey } from "@/features/assistant/api";
import { useDocuments } from "@/features/knowledge-base/hooks";
import { UsageSummary } from "@/features/usage/components/usage-stats";
import { useApiQuery } from "@/shared/api/hooks";
import { cn } from "@/shared/lib/format";
import { Card, CardBody, CardHeader, CopyField, IconTile, Progress, Stagger, StaggerItem } from "@/shared/ui";

function Step({ n, done, title, text, href }: { n: number; done: boolean; title: string; text: string; href?: string }) {
  const body = (
    <div className={cn("flex items-start gap-4 rounded-xl p-3 transition-colors", href && !done && "hover:bg-surface-muted")}>
      <span className={cn("grid size-8 shrink-0 place-items-center rounded-full text-sm font-semibold",
        done ? "bg-primary text-primary-fg" : "border-2 border-border-strong text-muted")}>
        {done ? <Check className="size-4" strokeWidth={3} /> : n}
      </span>
      <div className="min-w-0 flex-1 pt-0.5">
        <p className={cn("text-[15px] font-medium", done ? "text-muted" : "text-fg")}>{title}</p>
        <p className="text-sm text-subtle">{text}</p>
      </div>
      {href && !done && <ArrowRight className="mt-1.5 size-4 text-subtle" />}
    </div>
  );
  return <li>{href && !done ? <Link href={href}>{body}</Link> : body}</li>;
}

function CardLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link href={href} className="inline-flex items-center gap-1 text-sm font-medium text-primary-ink hover:underline">
      {children}<ArrowRight className="size-3.5" />
    </Link>
  );
}

export function OverviewPanel() {
  const docs = useDocuments();
  const assistant = useApiQuery(assistantKey, assistantApi.get);
  const total = docs.data?.documents.length ?? 0;
  const ready = docs.data?.documents.filter((d) => d.status === "READY").length ?? 0;
  const max = docs.data?.limits.max_documents ?? 10;

  return (
    <Stagger gap={0.06} className="space-y-6">
      <StaggerItem><UsageSummary /></StaggerItem>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <StaggerItem>
          <Card className="h-full">
            <CardHeader title="Get set up" description="Four steps to a live assistant." />
            <CardBody className="pt-3">
              <ol className="space-y-1">
                <Step n={1} done title="Create your organization" text="Your private workspace." />
                <Step n={2} done={total > 0} title="Upload policy PDFs" text="Up to 10 files, 20 pages each." href="/dashboard/knowledge-base" />
                <Step n={3} done={ready > 0} title="Wait for processing" text="Usually takes a few seconds." href="/dashboard/knowledge-base" />
                <Step n={4} done={false} title="Embed on your website" text="Copy a one-line snippet." href="/dashboard/assistant" />
              </ol>
            </CardBody>
          </Card>
        </StaggerItem>
        <StaggerItem>
          <Card className="h-full">
            <CardHeader icon={<IconTile><FileText /></IconTile>} title="Documents"
              description={`${ready} ready of ${max} allowed`} action={<CardLink href="/dashboard/knowledge-base">Manage</CardLink>} />
            <CardBody className="space-y-3">
              <p className="text-4xl font-semibold tabular-nums tracking-tight text-fg">
                {ready}<span className="text-xl font-medium text-subtle"> / {max}</span>
              </p>
              <Progress value={ready} max={max} />
              {total > ready && <p className="text-sm text-muted">{total - ready} processing or failed</p>}
            </CardBody>
          </Card>
        </StaggerItem>
      </div>

      {assistant.data && (
        <StaggerItem>
          <Card>
            <CardHeader icon={<IconTile><Bot /></IconTile>} title="Your assistant"
              description="Anyone with this link can ask questions." action={<CardLink href="/dashboard/assistant">Embed code</CardLink>} />
            <CardBody><CopyField label="assistant URL" value={assistant.data.assistant_url} /></CardBody>
          </Card>
        </StaggerItem>
      )}
    </Stagger>
  );
}
