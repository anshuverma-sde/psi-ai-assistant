import type { ErrorBody } from "./types";

/** Every failed API call surfaces as this one error type. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: Record<string, unknown> | null;
  readonly field?: string | null;
  readonly requestId?: string | null;

  constructor(status: number, body: ErrorBody, requestId?: string | null) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.details = body.details;
    this.field = body.field;
    this.requestId = requestId;
  }

  /** Field-level messages from VALIDATION_ERROR responses (or the single `field` of other errors). */
  get fieldErrors(): Record<string, string> {
    const fields = (this.details?.fields ?? {}) as Record<string, string>;
    if (this.field && !fields[this.field]) return { ...fields, [this.field]: this.message };
    return fields;
  }
}

export const NETWORK_ERROR: ErrorBody = {
  code: "NETWORK_ERROR",
  message: "Can't reach the server. Check your connection and try again.",
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}
