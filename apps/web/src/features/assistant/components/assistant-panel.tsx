"use client";

import { ArrowUpRight, Code2, Link2 } from "lucide-react";
import { useState } from "react";

import { useApiMutation, useApiQuery } from "@/shared/api/hooks";
import { formatDate } from "@/shared/lib/format";
import { Alert, Button, ButtonLink, Card, CardBody, CardHeader, ConfirmDialog, CopyField, IconTile, Skeleton, Stagger, StaggerItem } from "@/shared/ui";
import { assistantApi, assistantKey } from "../api";

export function AssistantPanel() {
  const { data, isLoading, error } = useApiQuery(assistantKey, assistantApi.get);
  const [confirming, setConfirming] = useState(false);
  const regenerate = useApiMutation(assistantApi.regenerate, {
    invalidate: [assistantKey],
    successMessage: "New link created. Update your embed code.",
    onSettled: () => setConfirming(false),
  });

  if (isLoading) return <Skeleton className="h-72 w-full" />;
  if (error || !data) return <Alert>{error?.message ?? "Couldn't load your assistant."}</Alert>;

  return (
    <Stagger gap={0.06} className="space-y-6">
      <StaggerItem>
        <Card>
          <CardHeader
            icon={<IconTile><Link2 /></IconTile>}
            title="Public link"
            description="No login needed. Visitors see answers — never your files."
            action={
              <ButtonLink href={data.assistant_url} target="_blank" rel="noreferrer" variant="secondary" size="sm">
                Open assistant<ArrowUpRight className="size-4" />
              </ButtonLink>
            }
          />
          <CardBody className="space-y-5">
            <CopyField label="assistant URL" value={data.assistant_url} />
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
              <p className="text-[13px] text-subtle">Link created {formatDate(data.rotated_at)}</p>
              <Button variant="secondary" size="sm" onClick={() => setConfirming(true)}>Regenerate link</Button>
            </div>
          </CardBody>
        </Card>
      </StaggerItem>

      <StaggerItem>
        <Card>
          <CardHeader icon={<IconTile><Code2 /></IconTile>} title="Embed on your website" description="Paste one snippet into any HTML page." />
          <CardBody className="space-y-5">
            <div className="space-y-2">
              <p className="text-sm font-medium text-fg">Floating chat button <span className="font-normal text-subtle">· recommended</span></p>
              <CopyField label="script embed code" value={data.embed.script} multiline />
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-fg">Inline frame</p>
              <CopyField label="iframe embed code" value={data.embed.iframe} multiline />
            </div>
          </CardBody>
        </Card>
      </StaggerItem>

      <ConfirmDialog
        open={confirming}
        title="Regenerate link?"
        description="The current link and every embed using it stop working right away."
        confirmLabel="Regenerate"
        loading={regenerate.isPending}
        onClose={() => setConfirming(false)}
        onConfirm={() => regenerate.mutate()}
      />
    </Stagger>
  );
}
