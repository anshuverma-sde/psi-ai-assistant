import { Loader2 } from "lucide-react";
import Link from "next/link";
import type { ButtonHTMLAttributes, ComponentProps } from "react";

import { cn } from "@/shared/lib/format";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "destructive" | "inverse";
type Size = "sm" | "md" | "lg" | "icon";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-primary text-primary-fg shadow-sm hover:bg-primary-hover",
  secondary: "bg-surface text-fg border border-border shadow-sm hover:border-border-strong hover:bg-surface-muted",
  ghost: "text-muted hover:bg-surface-muted hover:text-fg",
  danger: "text-danger hover:bg-danger-soft",
  destructive: "bg-danger text-danger-fg shadow-sm hover:bg-danger/90",
  inverse: "bg-surface text-primary-ink shadow-sm hover:bg-primary-soft",
};
const SIZES: Record<Size, string> = {
  sm: "h-9 px-3.5 text-sm gap-1.5",
  md: "h-10 px-4 text-sm gap-2",
  lg: "h-12 px-6 text-[15px] gap-2",
  icon: "size-9 justify-center",
};

/** Shared class builder so links and buttons look identical. */
export function buttonStyles({ variant = "primary", size = "md", className }: {
  variant?: Variant; size?: Size; className?: string;
} = {}) {
  return cn(
    "inline-flex shrink-0 items-center justify-center whitespace-nowrap rounded-lg font-medium",
    "transition-[background-color,border-color,color,box-shadow,transform] duration-150 active:scale-[0.98]",
    "disabled:pointer-events-none disabled:opacity-50",
    VARIANTS[variant],
    SIZES[size],
    className,
  );
}

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

export function Button({ variant, size, loading, disabled, className, children, type = "button", ...rest }: ButtonProps) {
  return (
    <button type={type} className={buttonStyles({ variant, size, className })} disabled={disabled || loading} {...rest}>
      {loading && <Loader2 className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

export function ButtonLink({ variant, size, className, ...rest }: ComponentProps<typeof Link> & { variant?: Variant; size?: Size }) {
  return <Link className={buttonStyles({ variant, size, className })} {...rest} />;
}
