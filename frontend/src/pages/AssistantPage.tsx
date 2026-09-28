import { useMemo } from "react";
import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  TextMessagePartProvider,
  ThreadPrimitive,
} from "@assistant-ui/react";
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";
import type { Components } from "react-markdown";
import { ArrowDown, Bot, Loader2, SendHorizontal, Sparkles, Wrench } from "lucide-react";

import { useAquaAssistant } from "@/assistant/runtime";
import { PageHeader } from "@/components/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { AssistantToolCall } from "@/types/analytics";

const SUGGESTIONS = [
  "Analyze today's water usage",
  "Which area wastes the most water?",
  "Explain peak consumption",
  "Compare Hubballi Central and Vidyanagar",
  "What percentage of supplied water is wasted?",
  "Forecast next 7 days",
  "Show the top anomalies",
  "How clean is the dataset?",
];

/** Tailwind-styled markdown renderer (tables, lists, emphasis…). */
const markdownComponents: Components = {
  table: (props) => (
    <div className="my-2 overflow-x-auto rounded-lg border bg-background/40">
      <table className="w-full border-collapse text-xs" {...props} />
    </div>
  ),
  th: (props) => <th className="border-b px-2 py-1.5 text-left font-semibold" {...props} />,
  td: (props) => <td className="border-b px-2 py-1.5 text-muted-foreground" {...props} />,
  ul: (props) => <ul className="my-1.5 list-disc space-y-1 pl-5" {...props} />,
  ol: (props) => <ol className="my-1.5 list-decimal space-y-1 pl-5" {...props} />,
  li: (props) => <li className="text-sm leading-relaxed" {...props} />,
  p: (props) => <p className="my-1.5 text-sm leading-relaxed" {...props} />,
  strong: (props) => <strong className="font-semibold text-foreground" {...props} />,
  h1: (props) => <h1 className="mt-3 mb-1 text-lg font-bold" {...props} />,
  h2: (props) => <h2 className="mt-3 mb-1 text-base font-bold" {...props} />,
  h3: (props) => <h3 className="mt-2 mb-1 text-sm font-bold" {...props} />,
  a: (props) => <a className="text-cyan-600 underline dark:text-cyan-400" {...props} />,
  code: (props) => (
    <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]" {...props} />
  ),
  pre: (props) => (
    <pre className="my-2 overflow-x-auto rounded-lg bg-muted p-3 font-mono text-xs" {...props} />
  ),
  hr: () => <hr className="my-3 border-border" />,
  blockquote: (props) => (
    <blockquote className="my-2 border-l-2 border-primary pl-3 italic text-muted-foreground" {...props} />
  ),
};

function ToolCalls({ toolCalls }: { toolCalls: AssistantToolCall[] }) {
  if (!toolCalls.length) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {toolCalls.map((tc) => (
        <span
          key={`${tc.name}-${JSON.stringify(tc.arguments).slice(0, 40)}`}
          className="inline-flex items-center gap-1 rounded-md border bg-muted/60 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground"
        >
          <Wrench className="size-2.5" />
          {tc.name}
        </span>
      ))}
    </div>
  );
}

export function AssistantPage() {
  const { runtime, messages, isRunning } = useAquaAssistant();
  const status = useApi(() => api.assistantStatus(), []);

  // Fast lookup of the external message (tool calls / error flag) by id.
  const byId = useMemo(() => new Map(messages.map((m) => [m.id, m])), [messages]);
  const mode = status.data?.mode ?? "local";

  return (
    <div>
      <PageHeader
        title="AquaAI Assistant"
        description="Ask questions about consumption, wastage, anomalies and forecasts — every answer is computed live from the analytical layer."
        actions={
          <Badge variant={mode === "llm" ? "success" : "default"} className="gap-1.5">
            <Sparkles className="size-3" />
            {mode === "llm" ? "LLM mode" : "local analytics mode"}
          </Badge>
        }
      />

      <Card className="mx-auto flex h-[calc(100vh-14rem)] min-h-[480px] max-w-3xl flex-col overflow-hidden">
        <AssistantRuntimeProvider runtime={runtime}>
          <ThreadPrimitive.Root>
          <ThreadPrimitive.Viewport className="relative flex-1 overflow-y-auto p-4" autoScroll>
            <div className="flex min-h-full flex-col">
              <div className="flex-1 space-y-4">
                {messages.length === 0 ? (
                  <EmptyState onPick={(q) => runtime.thread.append({ role: "user", content: [{ type: "text", text: q }] })} />
                ) : (
                  <>
                    <ThreadPrimitive.Messages>
                  {({ message }) => {
                    const ext = byId.get(message.id);
                    if (message.role === "user") {
                      return (
                        <div className="flex justify-end">
                          <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground">
                            {ext?.content ?? "(…)"}
                          </div>
                        </div>
                      );
                    }
                    return (
                      <div className="flex justify-start gap-2">
                        <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500 to-cyan-700 text-white">
                          <Bot className="size-4" />
                        </div>
                        <div
                          className={cn(
                            "max-w-[85%] rounded-2xl rounded-bl-sm border bg-card px-4 py-2.5",
                            ext?.error && "border-destructive/40 bg-destructive/5",
                          )}
                        >
                          <div className="mb-0.5 flex items-center gap-2">
                            <span className="text-[10px] font-semibold uppercase tracking-wider text-cyan-600 dark:text-cyan-400">
                              AquaAI
                            </span>
                            <span className="text-[10px] text-muted-foreground">{mode}</span>
                          </div>
                          <TextMessagePartProvider text={ext?.content ?? ""}>
                            <MarkdownTextPrimitive
                              smooth={false}
                              components={markdownComponents}
                              className="text-sm"
                            />
                          </TextMessagePartProvider>
                          {ext ? <ToolCalls toolCalls={ext.toolCalls} /> : null}
                        </div>
                      </div>
                    );
                  }}
                </ThreadPrimitive.Messages>

                {isRunning ? (
                  <div className="flex justify-start gap-2">
                    <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500 to-cyan-700 text-white">
                      <Bot className="size-4" />
                    </div>
                    <div className="flex items-center gap-2 rounded-2xl rounded-bl-sm border bg-card px-4 py-2.5 text-sm text-muted-foreground">
                      <Loader2 className="size-3.5 animate-spin" />
                      Analysing water data…
                    </div>
                  </div>
                ) : null}
                  </>
                )}
              </div>

              <ThreadPrimitive.ViewportFooter className="sticky bottom-0 mt-auto flex justify-center py-1">
                <ThreadPrimitive.ScrollToBottom aria-label="Scroll to bottom">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border bg-background shadow-sm">
                    <ArrowDown className="size-4" />
                  </div>
                </ThreadPrimitive.ScrollToBottom>
              </ThreadPrimitive.ViewportFooter>
            </div>
          </ThreadPrimitive.Viewport>

          <Composer className="border-t" />
          </ThreadPrimitive.Root>
        </AssistantRuntimeProvider>
      </Card>
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-5 p-6 text-center">
      <div className="flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-500 to-cyan-700 text-white shadow-lg shadow-cyan-500/25">
        <Bot className="size-7" />
      </div>
      <div>
        <h3 className="text-lg font-bold">Ask AquaAI about your water data</h3>
        <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
          Questions are answered in real time from the PySpark analytical layer — no canned or
          fabricated numbers.
        </p>
      </div>
      <div className="flex max-w-md flex-wrap justify-center gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onPick(s)}
            className="rounded-full border bg-background px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:border-cyan-500/60 hover:bg-cyan-500/10 hover:text-cyan-600 dark:hover:text-cyan-400"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

function Composer({ className }: { className?: string }) {
  return (
    <ComposerPrimitive.Root
      className={cn("flex items-end gap-2 bg-card/80 p-3 backdrop-blur", className)}
    >
      <ComposerPrimitive.Input
        className="max-h-40 min-h-11 flex-1 resize-none rounded-xl border bg-background px-3.5 py-2.5 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-primary/30"
        placeholder="e.g. Which area wastes the most water?"
        autoFocus
      />
      <ComposerPrimitive.Send asChild>
        <Button size="icon" className="size-11 shrink-0" aria-label="Send message">
          <SendHorizontal className="size-4" />
        </Button>
      </ComposerPrimitive.Send>
    </ComposerPrimitive.Root>
  );
}