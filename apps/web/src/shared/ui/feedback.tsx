"use client";

import { AlertCircle, CheckCircle2, Info, Loader2, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/shared/lib/format";
import { FadeIn, motion } from "./motion";

export type Tone = "neutral" | "primary" | "success" | "warning" | "danger";

const SOFT: Record<Tone, string> = {
  neutral: "bg-surface-muted text-muted",
  primary: "bg-primary-soft text-primary-ink",
  success: "bg-success-soft text-success",
  warning: "bg-warning-soft text-warning",
  danger: "bg-danger-soft text-danger",
};
const TEXT: Record<Tone, string> = {
  neutral: "text-fg", primary: "text-primary-ink", success: "text-success", warning: "text-warning", danger: "text-danger",
};
const DOT: Record<Tone, string> = {
  neutral: "bg-subtle", primary: "bg-primary-ink", success: "bg-success", warning: "bg-warning", danger: "bg-danger",
};

export function Badge({ tone = "neutral", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium", SOFT[tone], className)}>
      {children}
    </span>
  );
}

/** Small colored dot + label, optionally pulsing for in-progress states. */
export function StatusDot({ tone = "neutral", pulse, children }: { tone?: Tone; pulse?: boolean; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-[13px] text-muted">
      <span className="relative flex size-2">
        {pulse && <span className={cn("absolute inset-0 animate-ping rounded-full opacity-60", DOT[tone])} />}
        <span className={cn("relative size-2 rounded-full", DOT[tone])} />
      </span>
      {children}
    </span>
  );
}

/** Tinted rounded square holding an icon. */
export function IconTile({ tone = "primary", size = "md", children }: { tone?: Tone; size?: "sm" | "md" | "lg"; children: ReactNode }) {
  const sizes = { sm: "size-8 rounded-lg [&_svg]:size-4", md: "size-10 rounded-xl [&_svg]:size-5", lg: "size-12 rounded-xl [&_svg]:size-6" };
  return <div className={cn("grid shrink-0 place-items-center", SOFT[tone], sizes[size])}>{children}</div>;
}

export function Avatar({ name, size = "md", className }: { name: string; size?: "sm" | "md" | "lg"; className?: string }) {
  const sizes = { sm: "size-7 text-xs", md: "size-9 text-sm", lg: "size-12 text-lg" };
  return (
    <span aria-hidden className={cn("grid shrink-0 place-items-center rounded-full bg-brand-gradient font-semibold text-primary-fg", sizes[size], className)}>
      {name.trim().charAt(0).toUpperCase() || "?"}
    </span>
  );
}

export function Spinner({ label = "Loading", className }: { label?: string; className?: string }) {
  return (
    <div className={cn("flex items-center justify-center gap-2 py-16 text-sm text-subtle", className)} role="status">
      <Loader2 className="size-4 animate-spin" aria-hidden />
      {label}
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse rounded-xl bg-border/60", className)} aria-hidden />;
}

export function EmptyState({ icon, title, description, action }: {
  icon?: ReactNode; title: string; description?: string; action?: ReactNode;
}) {
  return (
    <FadeIn className="flex flex-col items-center px-6 py-16 text-center">
      {icon && <IconTile tone="neutral" size="lg">{icon}</IconTile>}
      <p className="mt-4 text-[15px] font-semibold text-fg">{title}</p>
      {description && <p className="mt-1 max-w-sm text-sm text-muted">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </FadeIn>
  );
}

const ALERT_ICON = { neutral: Info, primary: Info, success: CheckCircle2, warning: TriangleAlert, danger: AlertCircle };

export function Alert({ tone = "danger", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  const Icon = ALERT_ICON[tone];
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      role={tone === "danger" ? "alert" : "status"}
      className={cn("flex items-start gap-2.5 rounded-lg px-3.5 py-3 text-sm", SOFT[tone], className)}
    >
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="min-w-0">{children}</div>
    </motion.div>
  );
}

/** KPI card: icon tile + label + big number. */
export function StatCard({ label, value, hint, icon, tone = "primary" }: {
  label: string; value: ReactNode; hint?: string; icon: ReactNode; tone?: Tone;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-5 shadow-md">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted">{label}</p>
        <IconTile tone={tone} size="sm">{icon}</IconTile>
      </div>
      <p className={cn("mt-3 text-3xl font-semibold tabular-nums tracking-tight", TEXT.neutral)}>{value}</p>
      {hint && <p className="mt-1 text-[13px] text-subtle">{hint}</p>}
    </div>
  );
}

export function Progress({ value, max, tone = "primary" }: { value: number; max: number; tone?: Tone }) {
  const pct = max ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="h-2 overflow-hidden rounded-full bg-surface-muted" role="progressbar" aria-valuenow={value} aria-valuemax={max}>
      <motion.div
        className={cn("h-full rounded-full", DOT[tone])}
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      />
    </div>
  );
}
