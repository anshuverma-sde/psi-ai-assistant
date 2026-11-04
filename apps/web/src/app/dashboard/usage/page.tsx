import type { Metadata } from "next";

import { UsageStats } from "@/features/usage/components/usage-stats";
import { PageHeader } from "@/shared/ui";

export const metadata: Metadata = { title: "Usage" };

export default function UsagePage() {
  return (
    <>
      <PageHeader title="Usage" description="What visitors ask, and where your documents fall short." />
      <UsageStats />
    </>
  );
}
