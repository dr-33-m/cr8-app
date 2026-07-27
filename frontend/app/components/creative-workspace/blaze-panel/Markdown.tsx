import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * B.L.A.Z.E's replies, rendered as markdown.
 *
 * It writes markdown whether or not anything renders it — bold, bullet lists,
 * `code`, the occasional table — so plain text showed raw `**stars**`.
 *
 * react-markdown does not render raw HTML unless rehype-raw is added, which it
 * deliberately is not: the model's output is untrusted text and must never
 * become live markup. Links get noopener/noreferrer for the same reason.
 *
 * Elements are styled explicitly rather than via a prose plugin, because this
 * renders inside a narrow chat bubble where default typography is far too airy.
 */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="text-sm leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="my-2">{children}</p>,
          strong: ({ children }) => (
            <strong className="font-semibold">{children}</strong>
          ),
          em: ({ children }) => <em className="italic">{children}</em>,
          ul: ({ children }) => (
            <ul className="my-2 list-disc space-y-0.5 pl-4">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="my-2 list-decimal space-y-0.5 pl-4">{children}</ol>
          ),
          li: ({ children }) => <li className="pl-0.5">{children}</li>,
          h1: ({ children }) => (
            <h1 className="mb-1 mt-3 text-base font-semibold">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="mb-1 mt-3 text-sm font-semibold">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="mb-1 mt-2 text-sm font-semibold">{children}</h3>
          ),
          code: ({ className, children }) => {
            // Fenced blocks arrive with a language class; inline code does not.
            const isBlock = Boolean(className);
            if (isBlock) {
              return (
                <code className="block font-mono text-xs">{children}</code>
              );
            }
            return (
              <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            // Long lines scroll inside the block rather than widening the panel.
            <pre className="my-2 overflow-x-auto rounded-md bg-muted p-2">
              {children}
            </pre>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-2 hover:opacity-80"
            >
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote className="my-2 border-l-2 border-border pl-3 opacity-90">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="my-3 border-border" />,
          table: ({ children }) => (
            <div className="my-2 overflow-x-auto">
              <table className="w-full border-collapse text-xs">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-border px-2 py-1 text-left font-semibold">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-border px-2 py-1">{children}</td>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
