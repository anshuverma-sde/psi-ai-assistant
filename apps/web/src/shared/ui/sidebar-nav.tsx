"use client";

import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { cn } from "@/shared/lib/format";
import { motion } from "./motion";

export type NavItem = { href: string; label: string; icon: LucideIcon; exact?: boolean; badge?: ReactNode };

/** Vertical navigation with an animated active pill. In `collapsed` mode only icons show (labels become tooltips). */
export function SidebarNav({ items, label, collapsed = false, onNavigate }: {
  items: NavItem[]; label: string; collapsed?: boolean; onNavigate?: () => void;
}) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-1" aria-label={label}>
      {items.map(({ href, label: text, icon: Icon, exact, badge }) => {
        const active = exact ? pathname === href : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            title={collapsed ? text : undefined}
            aria-label={collapsed ? text : undefined}
            aria-current={active ? "page" : undefined}
            className={cn(
              "group relative flex items-center gap-3 rounded-lg py-2.5 text-sm font-medium transition-colors",
              collapsed ? "justify-center px-0" : "px-3",
              active ? "text-primary-ink" : "text-muted hover:bg-surface-muted hover:text-fg",
            )}
          >
            {active && (
              <motion.span layoutId={`${label}-active`} className="absolute inset-0 rounded-lg bg-primary-soft"
                transition={{ type: "spring", stiffness: 500, damping: 40 }}>
                <span className="absolute inset-y-2 left-0 w-[3px] rounded-r-full bg-primary-ink" />
              </motion.span>
            )}
            <Icon className="relative size-[18px] shrink-0" aria-hidden />
            {!collapsed && <span className="relative flex-1 truncate">{text}</span>}
            {badge != null && !collapsed && <span className="relative">{badge}</span>}
            {badge != null && collapsed && (
              <span className="absolute right-2.5 top-2 size-1.5 rounded-full bg-primary-ink" aria-hidden />
            )}
          </Link>
        );
      })}
    </nav>
  );
}
