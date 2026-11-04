"use client";

import { useState } from "react";

import { errorMessage } from "@/shared/api/errors";
import type { KnowledgeBaseLimits } from "@/shared/api/types";
import { Alert, AnimatePresence, FileDropzone, motion } from "@/shared/ui";
import { useUploadDocument } from "../hooks";

type Failure = { name: string; message: string };

export function UploadPanel({ limits }: { limits: KnowledgeBaseLimits }) {
  const upload = useUploadDocument();
  const [busy, setBusy] = useState(false);
  const [failures, setFailures] = useState<Failure[]>([]);
  const full = limits.remaining_documents === 0;

  // Sequential uploads, so each file gets its own validation result from the server.
  const onFiles = async (files: File[]) => {
    setBusy(true);
    setFailures([]);
    const failed: Failure[] = [];
    for (const file of files) {
      try {
        await upload.mutateAsync(file);
      } catch (err) {
        failed.push({ name: file.name, message: errorMessage(err) });
      }
    }
    setFailures(failed);
    setBusy(false);
  };

  return (
    <div className="space-y-3">
      <FileDropzone
        accept="application/pdf,.pdf"
        multiple
        busy={busy}
        disabled={full}
        onFiles={onFiles}
        title={full ? "Limit reached" : busy ? "Uploading…" : "Drop PDFs or click to upload"}
        hint={full ? "Delete or replace a document to add more" : `${limits.remaining_documents} remaining`}
      />
      <AnimatePresence>
        {failures.length > 0 && (
          <motion.ul initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-2" aria-live="polite">
            {failures.map((f) => (
              <li key={f.name}>
                <Alert><span className="font-medium">{f.name}</span> — {f.message}</Alert>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}
