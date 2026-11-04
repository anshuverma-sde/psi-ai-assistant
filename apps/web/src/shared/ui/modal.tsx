"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { fade, scaleIn } from "@/shared/lib/motion";
import { Button } from "./button";
import { AnimatePresence, motion } from "./motion";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: ReactNode;
  children?: ReactNode;
  footer?: ReactNode;
}

/** Animated, accessible modal (Esc / backdrop to close). Never a browser confirm() popup. */
export function Modal({ open, onClose, title, description, children, footer }: ModalProps) {
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    panel.current?.querySelector<HTMLElement>("button:not([disabled])")?.focus();
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
      previous?.focus();
    };
  }, [open, onClose]);

  if (typeof document === "undefined") return null;
  return createPortal(
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 grid place-items-center p-4">
          <motion.div variants={fade} initial="hidden" animate="show" exit="exit"
            className="absolute inset-0 bg-fg/20 backdrop-blur-[2px]" onClick={onClose} />
          <motion.div
            ref={panel}
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
            variants={scaleIn}
            initial="hidden"
            animate="show"
            exit="exit"
            className="relative w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-lg"
          >
            <h2 id="modal-title" className="text-lg font-semibold text-fg">{title}</h2>
            {description && <div className="mt-2 text-[15px] leading-relaxed text-muted">{description}</div>}
            {children}
            {footer && <div className="mt-6 flex justify-end gap-2">{footer}</div>}
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body,
  );
}

export function ConfirmDialog({ open, title, description, confirmLabel, tone = "danger", loading, onConfirm, onClose }: {
  open: boolean; title: string; description: ReactNode; confirmLabel: string;
  tone?: "danger" | "primary"; loading?: boolean; onConfirm: () => void; onClose: () => void;
}) {
  return (
    <Modal
      open={open}
      onClose={() => !loading && onClose()}
      title={title}
      description={description}
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button variant={tone === "danger" ? "destructive" : "primary"} onClick={onConfirm} loading={loading}>
            {confirmLabel}
          </Button>
        </>
      }
    />
  );
}
