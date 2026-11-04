"use client";

import {
  ArrowUpRight, BarChart3, Bot, FileText, LayoutGrid, LogOut, Menu, PanelLeftClose, PanelLeftOpen, X,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { assistantApi, assistantKey } from "@/features/assistant/api";
import { useLogout, useSession } from "@/features/auth/hooks";
import { useDocuments } from "@/features/knowledge-base/hooks";
import { usageApi, usageKey } from "@/features/usage/api";
import { useApiQuery } from "@/shared/api/hooks";
import { cn } from "@/shared/lib/format";
import { fade } from "@/shared/lib/motion";
import {
  AnimatePresence, Avatar, Badge, BrandMark, Button, FadeIn, motion, SidebarNav, Spinner, type NavItem,
} from "@/shared/ui";

const COLLAPSED_KEY = "psi.sidebar.collapsed";
const WIDTH = { open: 272, collapsed: 76 };

/** Remembers the collapsed state per browser; storage may be unavailable (private mode), so fail quietly. */
function useCollapsed(): [boolean, (v: boolean) => void] {
  const [collapsed, setCollapsed] = useState(false);
  useEffect(() => {
    try { setCollapsed(localStorage.getItem(COLLAPSED_KEY) === "1"); } catch { /* ignore */ }
  }, []);
  const update = (value: boolean) => {
    setCollapsed(value);
    try { localStorage.setItem(COLLAPSED_KEY, value ? "1" : "0"); } catch { /* ignore */ }
  };
  return [collapsed, update];
}

function useNavItems(): NavItem[] {
  const docs = useDocuments();
  const usage = useApiQuery(usageKey, usageApi.get, { refetchInterval: 30_000 });
  const ready = docs.data?.documents.filter((d) => d.status === "READY").length;
  const max = docs.data?.limits.max_documents;
  const review = usage.data?.needs_review ?? 0;
  return [
    { href: "/dashboard", label: "Overview", icon: LayoutGrid, exact: true },
    { href: "/dashboard/knowledge-base", label: "Documents", icon: FileText,
      badge: ready != null && max != null ? <span className="text-xs tabular-nums text-subtle">{ready}/{max}</span> : undefined },
    { href: "/dashboard/assistant", label: "Assistant", icon: Bot },
    { href: "/dashboard/usage", label: "Usage", icon: BarChart3,
      badge: review > 0 ? <Badge tone="warning" className="tabular-nums">{review}</Badge> : undefined },
  ];
}

function TryAssistantCard() {
  const { data } = useApiQuery(assistantKey, assistantApi.get);
  if (!data) return null;
  return (
    <div className="rounded-xl border border-primary-muted bg-primary-soft p-4">
      <p className="text-sm font-semibold text-fg">Try your assistant</p>
      <p className="mt-0.5 text-[13px] leading-snug text-muted">See exactly what your visitors see.</p>
      <a href={data.assistant_url} target="_blank" rel="noreferrer"
        className="mt-3 inline-flex items-center gap-1 text-[13px] font-semibold text-primary-ink hover:underline">
        Open assistant<ArrowUpRight className="size-3.5" />
      </a>
    </div>
  );
}

function SidebarContent({ org, email, collapsed, onToggle, onNavigate, onLogout, loggingOut }: {
  org: string; email: string; collapsed: boolean; onToggle?: () => void; onNavigate?: () => void;
  onLogout: () => void; loggingOut: boolean;
}) {
  const items = useNavItems();
  return (
    <div className="flex h-full flex-col">
      {/* Logo + collapse toggle */}
      <div className={cn("flex h-16 items-center", collapsed ? "justify-center" : "justify-between px-5")}>
        {collapsed ? (
          <button onClick={onToggle} title="Expand sidebar" aria-label="Expand sidebar"
            className="group relative grid size-9 place-items-center rounded-lg">
            <span className="transition-opacity group-hover:opacity-0"><BrandMark href="/dashboard" compact /></span>
            <PanelLeftOpen className="absolute size-[18px] text-muted opacity-0 transition-opacity group-hover:opacity-100" />
          </button>
        ) : (
          <>
            <BrandMark href="/dashboard" />
            {onToggle && (
              <Button variant="ghost" size="icon" onClick={onToggle} aria-label="Collapse sidebar" title="Collapse sidebar">
                <PanelLeftClose className="size-[18px]" />
              </Button>
            )}
          </>
        )}
      </div>

      {/* Workspace identity */}
      <div className={cn("mb-4", collapsed ? "flex justify-center" : "px-3")}>
        {collapsed ? (
          <span title={org}><Avatar name={org} /></span>
        ) : (
          <div className="flex items-center gap-3 rounded-xl border border-border bg-surface px-3 py-2.5 shadow-sm">
            <Avatar name={org} />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-fg" title={org}>{org}</p>
              <p className="text-xs text-subtle">Organization</p>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className={cn("flex-1 overflow-y-auto", collapsed ? "px-3" : "px-3")}>
        {!collapsed && <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-subtle">Workspace</p>}
        <SidebarNav items={items} label="Dashboard" collapsed={collapsed} onNavigate={onNavigate} />
      </div>

      {/* Quick action + account */}
      <div className="space-y-3 p-3">
        {!collapsed && <TryAssistantCard />}
        <div className={cn("flex items-center gap-2 border-t border-border pt-3", collapsed ? "justify-center" : "px-2")}>
          {!collapsed && <p className="min-w-0 flex-1 truncate text-[13px] text-muted" title={email}>{email}</p>}
          <Button variant="ghost" size="icon" onClick={onLogout} loading={loggingOut} aria-label="Log out" title="Log out">
            {!loggingOut && <LogOut className="size-4" />}
          </Button>
        </div>
      </div>
    </div>
  );
}

export function DashboardShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const session = useSession();
  const logout = useLogout();
  const [drawer, setDrawer] = useState(false);
  const [collapsed, setCollapsed] = useCollapsed();

  useEffect(() => {
    if (session.error?.status === 401) router.replace("/login");
  }, [session.error, router]);

  if (!session.data) return <Spinner className="min-h-dvh" label={session.error ? "Redirecting" : "Loading"} />;

  const common = {
    org: session.data.organization.name,
    email: session.data.user.email,
    onLogout: () => logout.mutate(),
    loggingOut: logout.isPending,
  };

  return (
    <div className="flex min-h-dvh">
      {/* Desktop sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: collapsed ? WIDTH.collapsed : WIDTH.open }}
        transition={{ type: "spring", stiffness: 380, damping: 38 }}
        className="sticky top-0 hidden h-dvh shrink-0 overflow-hidden border-r border-border bg-surface-muted/60 lg:block"
      >
        <SidebarContent {...common} collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      </motion.aside>

      <div className="min-w-0 flex-1">
        {/* Mobile top bar + drawer */}
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-border bg-background/90 px-4 backdrop-blur lg:hidden">
          <BrandMark href="/dashboard" />
          <Button variant="ghost" size="icon" onClick={() => setDrawer(true)} aria-label="Open menu"><Menu className="size-5" /></Button>
        </header>
        <AnimatePresence>
          {drawer && (
            <div className="fixed inset-0 z-40 lg:hidden">
              <motion.div variants={fade} initial="hidden" animate="show" exit="exit"
                className="absolute inset-0 bg-fg/30" onClick={() => setDrawer(false)} />
              <motion.aside
                initial={{ x: "-100%" }} animate={{ x: 0 }} exit={{ x: "-100%" }}
                transition={{ type: "spring", stiffness: 400, damping: 40 }}
                className="absolute inset-y-0 left-0 w-72 bg-background shadow-lg"
              >
                <Button variant="ghost" size="icon" className="absolute right-3 top-3.5 z-10" onClick={() => setDrawer(false)} aria-label="Close menu">
                  <X className="size-5" />
                </Button>
                <SidebarContent {...common} collapsed={false} onNavigate={() => setDrawer(false)} />
              </motion.aside>
            </div>
          )}
        </AnimatePresence>

        <main className="px-5 py-8 sm:px-10 lg:py-12">
          <FadeIn key={pathname} className="mx-auto max-w-6xl">{children}</FadeIn>
        </main>
      </div>
    </div>
  );
}
