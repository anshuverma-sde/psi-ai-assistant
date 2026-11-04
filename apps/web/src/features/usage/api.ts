import { api } from "@/shared/api/client";
import type { UsageOut } from "@/shared/api/types";

export const usageKey = ["usage"] as const;

export const usageApi = {
  get: (signal?: AbortSignal) => api.get<UsageOut>("/api/admin/usage", signal),
};
