import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { Source } from "@/shared/api/types";

/** Renders the answer; `[s2]` markers become numbered citation chips linked to the source list. */
export function AnswerMarkdown({ text, sources, messageId }: { text: string; sources: Source[]; messageId: string }) {
  const order = new Map(sources.map((s, i) => [s.id, i + 1]));
  // "…31 [s1]." → "…31. [s1]" so a citation chip never wraps onto a line by itself before the period.
  const punctuated = text.replace(/((?:\s*\[s\d+\])+)([.,;:])/g, "$2$1");
  const withLinks = punctuated.replace(/\s*\[(s\d+)\]/g, (_, id: string) =>
    order.has(id) ? `\u00a0[${id}](#cite-${messageId}-${id})` : "");

  return (
    <div className="prose-chat">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href = "", children }) => {
            const match = href.match(/^#cite-.+-(s\d+)$/);
            if (!match) {
              return <a href={href} target="_blank" rel="noreferrer" className="text-primary-ink underline underline-offset-2">{children}</a>;
            }
            const source = sources.find((s) => s.id === match[1]);
            return (
              <a
                href={href}
                title={source ? `${source.document} — Page ${source.page}` : undefined}
                className="inline-grid h-4 min-w-4 -translate-y-px place-items-center rounded bg-primary-soft px-1 align-middle text-[10px] font-medium text-primary-ink no-underline transition-colors hover:bg-primary-muted"
              >
                {order.get(match[1])}
              </a>
            );
          },
        }}
      >
        {withLinks}
      </ReactMarkdown>
    </div>
  );
}
