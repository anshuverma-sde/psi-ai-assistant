"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { useApiMutation, useApiQuery } from "@/shared/api/hooks";
import type { LoginIn, RegisterIn } from "@/shared/api/types";
import { authApi, sessionKey } from "./api";

export function useSession() {
  return useApiQuery(sessionKey, authApi.me, { staleTime: 60_000 });
}

function useAuthMutation<T>(fn: (body: T) => ReturnType<typeof authApi.login>) {
  const router = useRouter();
  const queryClient = useQueryClient();
  return useApiMutation(fn, {
    toastErrors: false, // shown inline on the form
    onSuccess: (session) => {
      queryClient.setQueryData(sessionKey, session);
      router.replace("/dashboard");
    },
  });
}

export const useLogin = () => useAuthMutation<LoginIn>(authApi.login);
export const useRegister = () => useAuthMutation<RegisterIn>(authApi.register);

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();
  return useApiMutation(authApi.logout, {
    onSuccess: () => {
      queryClient.clear();
      router.replace("/login");
    },
  });
}
