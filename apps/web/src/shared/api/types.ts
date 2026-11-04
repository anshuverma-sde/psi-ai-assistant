import type { components } from "./schema.gen";

/** Friendly aliases over the types generated from FastAPI's OpenAPI schema (`pnpm gen:api`). */
type S = components["schemas"];

export type ErrorBody = S["ErrorBody"];
export type Meta = S["Meta"];
export type ApiEnvelope<T> = { success: boolean; data: T | null; error: ErrorBody | null; meta: Meta };

export type SessionOut = S["SessionOut"];
export type RegisterIn = S["RegisterIn"];
export type LoginIn = S["LoginIn"];

export type DocumentOut = S["DocumentOut"];
export type DocumentListOut = S["DocumentListOut"];
export type KnowledgeBaseLimits = S["KnowledgeBaseLimits"];
export type Deleted = S["Deleted"];

export type AssistantOut = S["AssistantOut"];
export type PublicAssistantOut = S["PublicAssistantOut"];
export type AskIn = S["AskIn"];
export type AskOut = S["AskOut"];
export type DecisionResult = S["DecisionResult"];
export type ConditionTrace = S["ConditionTrace"];
export type Verdict = S["Verdict"];
export type Source = S["Source"];

export type UsageOut = S["UsageOut"];
