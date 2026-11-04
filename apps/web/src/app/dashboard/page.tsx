import type { Metadata } from "next";

import { OverviewPanel } from "@/features/dashboard/overview-panel";
import { PageHeader } from "@/shared/ui";

export const metadata: Metadata = { title: "Overview" };

export default function DashboardPage() {
  return (
    <>
      <PageHeader title="Overview" />
      <OverviewPanel />
    </>
  );
}
