import type { Metadata } from "next";

import { AssistantPanel } from "@/features/assistant/components/assistant-panel";
import { PageHeader } from "@/shared/ui";

export const metadata: Metadata = { title: "Assistant" };

export default function AssistantPage() {
  return (
    <>
      <PageHeader title="Assistant" description="Share the link or embed it on any website." />
      <AssistantPanel />
    </>
  );
}
