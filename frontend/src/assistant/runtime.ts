/** AquaAI chat runtime — external-store bridge between assistant-ui and the FastAPI backend. */

import { useCallback, useRef, useState } from "react";
import { useExternalStoreRuntime } from "@assistant-ui/react";
import type { AppendMessage, ThreadMessageLike } from "@assistant-ui/react";

import { api, ApiError } from "@/lib/api";
import type { AssistantToolCall } from "@/types/analytics";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls: AssistantToolCall[];
  error: boolean;
  createdAt: number;
}

let counter = 0;
function nextId(): string {
  counter += 1;
  return `m_${Date.now()}_${counter}`;
}

/**
 * Drives the assistant-ui external-store runtime from a plain array of
 * messages. `onNew` appends the user message optimistically, POSTs the turn to
 * `/api/assistant/chat`, then appends the assistant reply (markdown).
 */
export function useAquaAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const runningRef = useRef(isRunning);
  runningRef.current = isRunning;

  const messagesRef = useRef<ChatMessage[]>([]);
  messagesRef.current = messages;

  const convertMessage = useCallback((message: ChatMessage): ThreadMessageLike => {
    return {
      role: message.role,
      id: message.id,
      createdAt: new Date(message.createdAt),
      content: [{ type: "text", text: message.content }],
    };
  }, []);

  const onNew = useCallback(async (append: AppendMessage): Promise<void> => {
    if (runningRef.current) return;
    const text = append.content
      .filter((part) => part.type === "text")
      .map((part) => part.text)
      .join("")
      .trim();
    if (!text) return;

    // History = everything sent so far (no user message with empty content).
    const history = messagesRef.current.map((m) => ({ role: m.role, content: m.content }));

    const userMsg: ChatMessage = {
      id: nextId(),
      role: "user",
      content: text,
      toolCalls: [],
      error: false,
      createdAt: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);

    setIsRunning(true);
    try {
      const res = await api.assistantChat({ content: text, history });
      const reply: ChatMessage = {
        id: nextId(),
        role: "assistant",
        content: res.message,
        toolCalls: res.tool_calls ?? [],
        error: false,
        createdAt: Date.now(),
      };
      setMessages((prev) => [...prev, reply]);
    } catch (e) {
      const reply: ChatMessage = {
        id: nextId(),
        role: "assistant",
        content:
          e instanceof ApiError
            ? `**AquaAI error:** ${e.message}`
            : "**AquaAI error:** the analytics service did not respond. Is the backend running?",
        toolCalls: [],
        error: true,
        createdAt: Date.now(),
      };
      setMessages((prev) => [...prev, reply]);
    } finally {
      setIsRunning(false);
    }
  }, []);

  const runtime = useExternalStoreRuntime({
    messages,
    isRunning,
    convertMessage,
    onNew,
    setMessages: (next) => setMessages([...(next as ChatMessage[])]),
  });

  return { runtime, messages, isRunning };
}