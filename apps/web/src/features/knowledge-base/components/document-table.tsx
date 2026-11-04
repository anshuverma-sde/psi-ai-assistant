"use client";

import { FileText } from "lucide-react";
import { useRef, useState } from "react";

import type { DocumentOut } from "@/shared/api/types";
import { formatBytes, formatDate } from "@/shared/lib/format";
import { AnimatePresence, Button, ConfirmDialog, EmptyState, IconTile, MotionItem } from "@/shared/ui";
import { useDeleteDocument, useReplaceDocument } from "../hooks";
import { StatusBadge } from "./status-badge";

function DocumentRow({ doc, onDelete }: { doc: DocumentOut; onDelete: (doc: DocumentOut) => void }) {
  const replace = useReplaceDocument();
  const input = useRef<HTMLInputElement>(null);
  const meta = [
    `${doc.page_count} ${doc.page_count === 1 ? "page" : "pages"}`,
    formatBytes(doc.size_bytes),
    formatDate(doc.updated_at),
  ].join(" · ");

  return (
    <MotionItem className="flex flex-col gap-3 px-6 py-4 transition-colors hover:bg-surface-muted/60 sm:flex-row sm:items-center">
      <div className="flex min-w-0 flex-1 items-center gap-4">
        <IconTile tone={doc.status === "FAILED" ? "danger" : "primary"}><FileText /></IconTile>
        <div className="min-w-0 space-y-1">
          <p className="truncate text-[15px] font-medium text-fg">{doc.original_name}</p>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <StatusBadge status={doc.status} />
            <span className="text-[13px] text-subtle">{meta}</span>
          </div>
          {doc.status === "FAILED" && doc.error_message && <p className="text-[13px] text-danger">{doc.error_message}</p>}
        </div>
      </div>
      <div className="flex shrink-0 gap-1 pl-14 sm:pl-0">
        <input
          ref={input}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) replace.mutate({ id: doc.id, file });
            e.target.value = "";
          }}
        />
        <Button variant="ghost" size="sm" loading={replace.isPending} onClick={() => input.current?.click()}>Replace</Button>
        <Button variant="danger" size="sm" onClick={() => onDelete(doc)}>Delete</Button>
      </div>
    </MotionItem>
  );
}

export function DocumentTable({ documents }: { documents: DocumentOut[] }) {
  const remove = useDeleteDocument();
  const [pending, setPending] = useState<DocumentOut | null>(null);

  if (documents.length === 0) {
    return (
      <EmptyState
        icon={<FileText />}
        title="No documents yet"
        description="Upload handbooks, policies or FAQs. The assistant answers only from these."
      />
    );
  }

  return (
    <>
      <ul className="divide-y divide-border">
        <AnimatePresence initial={false}>
          {documents.map((doc) => <DocumentRow key={doc.id} doc={doc} onDelete={setPending} />)}
        </AnimatePresence>
      </ul>
      <ConfirmDialog
        open={!!pending}
        title="Delete document?"
        description={<>“{pending?.original_name}” will be removed and the assistant will stop using it.</>}
        confirmLabel="Delete"
        loading={remove.isPending}
        onClose={() => setPending(null)}
        onConfirm={() => pending && remove.mutate(pending.id, { onSettled: () => setPending(null) })}
      />
    </>
  );
}
