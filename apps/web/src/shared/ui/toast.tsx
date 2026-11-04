"use client";

import { CheckCircle2, X, XCircle } from "lucide-react";
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

import { scaleIn } from "@/shared/lib/motion";
import { AnimatePresence, motion } from "./motion";

type ToastItem = { id: number; tone: "success" | "error"; message: string };
type ToastApi = { success: (message: string) => void; error: (message: string) => void };

const ToastContext = createContext<ToastApi | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: number) => setItems((all) => all.filter((t) => t.id !== id)), []);
  const push = useCallback((tone: ToastItem["tone"], message: string) => {
    const id = Date.now() + Math.random();
    setItems((all) => [...all.slice(-2), { id, tone, message }]);
    setTimeout(() => dismiss(id), tone === "error" ? 6000 : 3000);
  }, [dismiss]);

  const api = useMemo<ToastApi>(() => ({ success: (m) => push("success", m), error: (m) => push("error", m) }), [push]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-5 z-50 flex flex-col items-center gap-2 px-4" aria-live="polite">
        <AnimatePresence initial={false}>
          {items.map((t) => (
            <motion.div
              key={t.id}
              layout
              variants={scaleIn}
              initial="hidden"
              animate="show"
              exit="exit"
              className="pointer-events-auto flex w-full max-w-sm items-center gap-2.5 rounded-xl border border-border bg-surface px-4 py-3 text-sm text-fg shadow-lg"
            >
              {t.tone === "success"
                ? <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden />
                : <XCircle className="size-4 shrink-0 text-danger" aria-hidden />}
              <p className="flex-1">{t.message}</p>
              <button onClick={() => dismiss(t.id)} className="text-subtle transition-colors hover:text-fg" aria-label="Dismiss">
                <X className="size-3.5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}
