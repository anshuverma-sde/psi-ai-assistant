import { api } from "@/shared/api/client";
import type { AskOut, PublicAssistantOut } from "@/shared/api/types";

export const chatApi = {
  info: (token: string, signal?: AbortSignal) =>
    api.get<PublicAssistantOut>(`/api/public/assistant/${encodeURIComponent(token)}`, signal),
  ask: (token: string, question: string, previousQuestion?: string | null) =>
    api.post<AskOut>("/api/ask", { token, question, previous_question: previousQuestion ?? null }),
};
