"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryKey,
  type UseMutationOptions,
  type UseQueryOptions,
} from "@tanstack/react-query";

import { useToast } from "@/shared/ui/toast";
import { ApiError, errorMessage } from "./errors";

/** Query wrapper: typed ApiError, no retries on 4xx. */
export function useApiQuery<T>(
  key: QueryKey,
  fn: (signal: AbortSignal) => Promise<T>,
  options: Omit<UseQueryOptions<T, ApiError>, "queryKey" | "queryFn"> = {},
) {
  return useQuery<T, ApiError>({
    queryKey: key,
    queryFn: ({ signal }) => fn(signal),
    retry: (count, error) => !(error instanceof ApiError && error.status >= 400 && error.status < 500) && count < 2,
    ...options,
  });
}

/** Mutation wrapper: shows a toast for errors (and optional success text), invalidates given keys. */
export function useApiMutation<TData, TVars = void>(
  fn: (vars: TVars) => Promise<TData>,
  {
    invalidate = [],
    successMessage,
    toastErrors = true,
    ...options
  }: Omit<UseMutationOptions<TData, ApiError, TVars>, "mutationFn"> & {
    invalidate?: QueryKey[];
    successMessage?: string | ((data: TData) => string);
    toastErrors?: boolean;
  } = {},
) {
  const queryClient = useQueryClient();
  const toast = useToast();
  return useMutation<TData, ApiError, TVars>({
    mutationFn: fn,
    ...options,
    onSuccess: async (data, vars, ctx, mctx) => {
      await Promise.all(invalidate.map((queryKey) => queryClient.invalidateQueries({ queryKey })));
      if (successMessage) toast.success(typeof successMessage === "function" ? successMessage(data) : successMessage);
      await options.onSuccess?.(data, vars, ctx, mctx);
    },
    onError: (error, vars, ctx, mctx) => {
      if (toastErrors) toast.error(errorMessage(error));
      options.onError?.(error, vars, ctx, mctx);
    },
  });
}
