"use client";

import { ArrowUp, CornerDownRight, MessageCircleQuestion, X } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";

import { useApiQuery } from "@/shared/api/hooks";
import { cn } from "@/shared/lib/format";
import { AnimatePresence, Avatar, motion, Spinner, Stagger, StaggerItem } from "@/shared/ui";
import { chatApi } from "../api";
import { useChat } from "../use-chat";
import { MessageBubble, TypingIndicator } from "./message-bubble";

const MAX_CHARS = 1000;

export function ChatApp({ token, embedded }: { token: string; embedded: boolean }) {
  const info = useApiQuery(["assistant-info", token], (signal) => chatApi.info(token, signal));
  const { messages, pending, ask, followUp, cancelFollowUp } = useChat(token);
  const [draft, setDraft] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  const textarea = useRef<HTMLTextAreaElement>(null);

  useEffect(() => bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" }), [messages, pending]);

  // Auto-grow the composer up to a few lines.
  useEffect(() => {
    const el = textarea.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
  }, [draft]);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    if (!draft.trim() || pending) return;
    ask(draft);
    setDraft("");
  };
  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) submit(e);
  };

  if (info.isLoading) return <Spinner className="h-dvh" />;
  if (info.error) {
    return (
      <div className="grid h-dvh place-items-center px-6 text-center">
        <div className="space-y-1">
          <p className="text-base font-semibold text-fg">This assistant isn&apos;t available</p>
          <p className="text-sm text-muted">{info.error.message}</p>
        </div>
      </div>
    );
  }

  const orgName = info.data?.organization_name ?? "Assistant";
  const suggestions = info.data?.suggested_questions ?? [];
  const empty = messages.length === 0;

  return (
    <div className="flex h-dvh flex-col bg-background">
      <header className={cn("flex items-center gap-3 border-b border-border bg-surface px-5", embedded ? "h-14" : "h-16")}>
        <Avatar name={orgName} />
        <div className="min-w-0">
          <h1 className="truncate text-[15px] font-semibold text-fg">{orgName}</h1>
          <p className="flex items-center gap-1.5 text-[13px] text-muted">
            <span className="size-1.5 rounded-full bg-success" aria-hidden />Answers from official documents
          </p>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl space-y-8 px-5 py-8" aria-live="polite">
          {empty && (
            <Stagger gap={0.07} className="flex flex-col items-center pt-[8vh] text-center">
              <StaggerItem><Avatar name={orgName} size="lg" className="shadow-lg" /></StaggerItem>
              <StaggerItem>
                <h2 className="mt-5 text-2xl font-semibold tracking-tight text-fg">How can I help you today?</h2>
              </StaggerItem>
              <StaggerItem>
                <p className="mx-auto mt-2 max-w-md text-[15px] text-muted">
                  Ask about {orgName}&apos;s policies. Every answer links to its source, and I&apos;ll say so if I don&apos;t know.
                </p>
              </StaggerItem>
              {!info.data?.ready && (
                <StaggerItem><p className="mt-4 text-sm text-warning">No documents have been published yet.</p></StaggerItem>
              )}
              {suggestions.length > 0 && (
                <StaggerItem className="mt-8 grid w-full gap-3 sm:grid-cols-3">
                  {suggestions.map((s) => (
                    <button key={s} onClick={() => ask(s)}
                      className="group flex flex-col items-start gap-3 rounded-xl border border-border bg-surface p-4 text-left text-sm text-fg shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary-muted hover:shadow-md">
                      <MessageCircleQuestion className="size-4 text-primary-ink" aria-hidden />
                      {s}
                    </button>
                  ))}
                </StaggerItem>
              )}
            </Stagger>
          )}
          {messages.map((m) => <MessageBubble key={m.id} message={m} orgName={orgName} />)}
          <AnimatePresence>{pending && <TypingIndicator orgName={orgName} />}</AnimatePresence>
          <div ref={bottom} />
        </div>
      </div>

      <form onSubmit={submit} className="bg-gradient-to-t from-background via-background px-5 pb-4 pt-2">
        <AnimatePresence>
          {followUp && (
            <motion.div
              initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }}
              className="mx-auto mb-2 flex w-full max-w-3xl items-center gap-2 rounded-xl border border-primary-muted bg-primary-soft px-3.5 py-2 text-[13px]"
            >
              <CornerDownRight className="size-3.5 shrink-0 text-primary-ink" aria-hidden />
              <p className="min-w-0 flex-1 truncate text-muted">
                Answering: <span className="text-fg">&ldquo;{followUp}&rdquo;</span>
              </p>
              <button type="button" onClick={cancelFollowUp} aria-label="Ask a new question instead"
                title="Ask a new question instead" className="text-subtle transition-colors hover:text-fg">
                <X className="size-3.5" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
        <div className="mx-auto flex w-full max-w-3xl items-end gap-3 rounded-2xl border border-border bg-surface px-4 py-3 shadow-md transition-[border-color,box-shadow] focus-within:border-primary-ink focus-within:ring-4 focus-within:ring-ring">
          <textarea
            ref={textarea}
            value={draft}
            onChange={(e) => setDraft(e.target.value.slice(0, MAX_CHARS))}
            onKeyDown={onKeyDown}
            rows={1}
            placeholder={followUp ? "Add the missing details…" : "Ask a question…"}
            aria-label="Your question"
            className="max-h-32 min-h-6 flex-1 resize-none bg-transparent py-1 text-[15px] text-fg outline-none placeholder:text-subtle"
          />
          <button
            type="submit"
            disabled={!draft.trim() || pending}
            aria-label="Send"
            className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary text-primary-fg shadow-sm transition-all hover:bg-primary-hover active:scale-95 disabled:bg-surface-muted disabled:text-subtle disabled:shadow-none"
          >
            <ArrowUp className="size-[18px]" />
          </button>
        </div>
        <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-subtle">AI answers can be imperfect — check the sources.</p>
      </form>
    </div>
  );
}
