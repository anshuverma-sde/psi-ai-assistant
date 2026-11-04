import type { Metadata } from "next";

import { ChatApp } from "@/features/chat/components/chat-app";

export const metadata: Metadata = { title: "Assistant", robots: { index: false } };

export default async function AssistantChatPage({
  params,
  searchParams,
}: {
  params: Promise<{ token: string }>;
  searchParams: Promise<{ embed?: string }>;
}) {
  const [{ token }, { embed }] = await Promise.all([params, searchParams]);
  return <ChatApp token={token} embedded={embed === "1"} />;
}
