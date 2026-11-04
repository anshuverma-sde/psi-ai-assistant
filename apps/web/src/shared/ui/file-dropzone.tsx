"use client";

import { Upload } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

import { cn } from "@/shared/lib/format";
import { motion } from "./motion";

interface FileDropzoneProps {
  accept: string;
  multiple?: boolean;
  disabled?: boolean;
  busy?: boolean;
  title: ReactNode;
  hint?: ReactNode;
  onFiles: (files: File[]) => void;
}

export function FileDropzone({ accept, multiple, disabled, busy, title, hint, onFiles }: FileDropzoneProps) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const inactive = disabled || busy;

  const handle = (list: FileList | null) => {
    if (!list?.length || inactive) return;
    onFiles(Array.from(list));
    if (input.current) input.current.value = "";
  };
  const open = () => !inactive && input.current?.click();

  return (
    <motion.div
      role="button"
      tabIndex={inactive ? -1 : 0}
      aria-disabled={inactive}
      onClick={open}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && open()}
      onDragOver={(e) => { e.preventDefault(); if (!inactive) setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => { e.preventDefault(); setOver(false); handle(e.dataTransfer.files); }}
      animate={{ scale: over ? 1.01 : 1 }}
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors",
        inactive ? "cursor-not-allowed border-border opacity-60"
          : over ? "cursor-copy border-primary-ink bg-primary-soft"
          : "cursor-pointer border-border-strong hover:border-primary-ink hover:bg-primary-soft/50",
      )}
    >
      <motion.div
        animate={busy ? { y: [0, -3, 0] } : { y: 0 }}
        transition={busy ? { repeat: Infinity, duration: 1 } : undefined}
        className="mb-3 grid size-11 place-items-center rounded-xl bg-primary-soft text-primary-ink"
      >
        <Upload className="size-5" aria-hidden />
      </motion.div>
      <p className="text-[15px] font-medium text-fg">{title}</p>
      {hint && <p className="mt-1 text-[13px] text-subtle">{hint}</p>}
      <input ref={input} type="file" accept={accept} multiple={multiple} className="hidden" onChange={(e) => handle(e.target.files)} />
    </motion.div>
  );
}
