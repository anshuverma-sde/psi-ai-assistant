"use client";

import { useCallback, useRef, useState } from "react";

import { ApiError } from "@/shared/api/errors";
import type { AskOut } from "@/shared/api/types";
import { chatApi } from "./api";

export type ChatMessage =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "assistant"; result: AskOut }
  | { id: string; role: "error"; text: string; code: string };

const uid = () => Math.random().toString(36).slice(2);

export function useChat(token: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  // When the assistant asks for missing details, the next message is sent as a reply to this question.
  const [followUp, setFollowUp] = useState<string | null>(null);
  const followUpRef = useRef<string | null>(null);
  const inFlight = useRef(false);

  const updateFollowUp = useCallback((value: string | null) => {
    followUpRef.current = value;
    setFollowUp(value);
  }, []);

  const ask = useCallback(async (question: string) => {
    const text = question.trim();
    if (!text || inFlight.current) return;
    inFlight.current = true;
    setPending(true);
    setMessages((m) => [...m, { id: uid(), role: "user", text }]);
    try {
      const result = await chatApi.ask(token, text, followUpRef.current);
      setMessages((m) => [...m, { id: uid(), role: "assistant", result }]);
      updateFollowUp(result.status === "needs_info" ? result.resolved_question : null);
    } catch (err) {
      const e = err instanceof ApiError ? err : null;
      setMessages((m) => [...m, {
        id: uid(), role: "error", code: e?.code ?? "UNKNOWN",
        text: e?.message ?? "Something went wrong. Please try again.",
      }]);
    } finally {
      inFlight.current = false;
      setPending(false);
    }
  }, [token, updateFollowUp]);

  const cancelFollowUp = useCallback(() => updateFollowUp(null), [updateFollowUp]);

  return { messages, pending, ask, followUp, cancelFollowUp };
}
