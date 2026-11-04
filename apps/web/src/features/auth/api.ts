import { api } from "@/shared/api/client";
import type { LoginIn, RegisterIn, SessionOut } from "@/shared/api/types";

export const sessionKey = ["session"] as const;

export const authApi = {
  me: (signal?: AbortSignal) => api.get<SessionOut>("/api/auth/me", signal),
  login: (body: LoginIn) => api.post<SessionOut>("/api/auth/login", body),
  register: (body: RegisterIn) => api.post<SessionOut>("/api/auth/register", body),
  logout: () => api.post<{ logged_out: boolean }>("/api/auth/logout"),
};
