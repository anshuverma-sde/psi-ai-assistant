import { api } from "@/shared/api/client";
import type { AssistantOut } from "@/shared/api/types";

export const assistantKey = ["assistant"] as const;

export const assistantApi = {
  get: (signal?: AbortSignal) => api.get<AssistantOut>("/api/admin/assistant", signal),
  regenerate: () => api.post<AssistantOut>("/api/admin/assistant/regenerate"),
};
