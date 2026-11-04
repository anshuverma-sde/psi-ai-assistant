import { ApiError, NETWORK_ERROR } from "./errors";
import type { ApiEnvelope } from "./types";

type Method = "GET" | "POST" | "PUT" | "DELETE";

interface RequestOptions {
  method?: Method;
  json?: unknown;
  form?: FormData;
  signal?: AbortSignal;
}

/**
 * Calls the API (same origin, proxied by Next.js) and unwraps the standard envelope:
 * returns `data` on success, throws `ApiError` otherwise.
 */
export async function apiFetch<T>(path: string, { method = "GET", json, form, signal }: RequestOptions = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      method,
      signal,
      credentials: "same-origin",
      headers: json !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: json !== undefined ? JSON.stringify(json) : form,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") throw err;
    throw new ApiError(0, NETWORK_ERROR);
  }

  const requestId = response.headers.get("x-request-id");
  let envelope: ApiEnvelope<T> | null = null;
  try {
    envelope = (await response.json()) as ApiEnvelope<T>;
  } catch {
    /* non-JSON (e.g. proxy error page) */
  }

  if (!envelope || typeof envelope.success !== "boolean") {
    throw new ApiError(response.status, {
      code: response.status === 413 ? "PDF_TOO_LARGE" : "INTERNAL_ERROR",
      message: response.status === 413 ? "The file is too large." : "Unexpected response from the server.",
    }, requestId);
  }
  if (!envelope.success || envelope.error) {
    throw new ApiError(response.status, envelope.error ?? { code: "INTERNAL_ERROR", message: "Request failed." },
      envelope.meta?.request_id ?? requestId);
  }
  return envelope.data as T;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => apiFetch<T>(path, { signal }),
  post: <T>(path: string, json?: unknown) => apiFetch<T>(path, { method: "POST", json: json ?? {} }),
  put: <T>(path: string, json?: unknown) => apiFetch<T>(path, { method: "PUT", json }),
  delete: <T>(path: string) => apiFetch<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, file: File, method: Method = "POST") => {
    const form = new FormData();
    form.append("file", file);
    return apiFetch<T>(path, { method, form });
  },
};
