"use client";

import { fadeUp } from "@/shared/lib/motion";
import { Alert, Avatar, Badge, motion } from "@/shared/ui";
import type { ChatMessage } from "../use-chat";
import { AnswerMarkdown } from "./answer-markdown";
import { DecisionTrace } from "./decision-trace";
import { SourceList } from "./source-list";

const STATUS_NOTE: Partial<Record<string, { tone: "warning" | "danger"; text: string }>> = {
  no_answer: { tone: "warning", text: "Not in the documents" },
  needs_review: { tone: "danger", text: "Partial answer" },
};

export function MessageBubble({ message, orgName }: { message: ChatMessage; orgName: string }) {
  return (
    <motion.div variants={fadeUp} initial="hidden" animate="show" layout="position">
      {message.role === "user" ? (
        <div className="flex justify-end">
          <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-primary px-4 py-3 text-[15px] text-primary-fg shadow-sm">{message.text}</p>
        </div>
      ) : message.role === "error" ? (
        <Alert>{message.text}</Alert>
      ) : (
        <AssistantAnswer message={message} orgName={orgName} />
      )}
    </motion.div>
  );
}

function AssistantAnswer({ message, orgName }: { message: Extract<ChatMessage, { role: "assistant" }>; orgName: string }) {
  const r = message.result;
  const note = STATUS_NOTE[r.status];
  return (
    <div className="flex items-start gap-3">
      <Avatar name={orgName} size="sm" className="mt-0.5" />
      <div className="min-w-0 flex-1 rounded-2xl rounded-tl-md border border-border bg-surface px-5 py-4 shadow-sm">
        {note && <Badge tone={note.tone} className="mb-2">{note.text}</Badge>}
        <AnswerMarkdown text={r.answer} sources={r.sources} messageId={message.id} />
        {r.verdict && r.decisions.length > 0 && <DecisionTrace verdict={r.verdict} decisions={r.decisions} sources={r.sources} />}
        <SourceList sources={r.sources} messageId={message.id} />
      </div>
    </div>
  );
}

export function TypingIndicator({ orgName }: { orgName: string }) {
  return (
    <motion.div variants={fadeUp} initial="hidden" animate="show" exit="exit" className="flex items-center gap-3">
      <Avatar name={orgName} size="sm" />
      <div className="flex items-center gap-2.5 rounded-2xl rounded-tl-md border border-border bg-surface px-4 py-3 text-sm text-muted shadow-sm">
        <span className="flex gap-1" aria-hidden>
          {[0, 1, 2].map((i) => (
            <motion.span key={i} className="size-1.5 rounded-full bg-primary-ink"
              animate={{ opacity: [0.25, 1, 0.25], y: [0, -2, 0] }} transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.15 }} />
          ))}
        </span>
        Checking the documents…
      </div>
    </motion.div>
  );
}
