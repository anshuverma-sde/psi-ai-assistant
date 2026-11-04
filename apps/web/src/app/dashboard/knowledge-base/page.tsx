import type { Metadata } from "next";

import { KnowledgeBasePanel } from "@/features/knowledge-base/components/knowledge-base-panel";
import { PageHeader } from "@/shared/ui";

export const metadata: Metadata = { title: "Documents" };

export default function KnowledgeBasePage() {
  return (
    <>
      <PageHeader title="Documents" description="Your assistant answers only from documents marked ready." />
      <KnowledgeBasePanel />
    </>
  );
}
