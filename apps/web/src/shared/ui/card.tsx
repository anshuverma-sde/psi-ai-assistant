import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/shared/lib/format";

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-xl border border-border bg-surface shadow-md", className)} {...rest} />;
}

export function CardHeader({ title, description, action, icon, className }: {
  title: ReactNode; description?: ReactNode; action?: ReactNode; icon?: ReactNode; className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap items-start justify-between gap-4 px-6 pt-6", className)}>
      <div className="flex min-w-0 items-start gap-3">
        {icon}
        <div className="min-w-0 space-y-1">
          <h2 className="text-base font-semibold text-fg">{title}</h2>
          {description && <p className="text-sm text-muted">{description}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

export function CardBody({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6", className)} {...rest} />;
}
