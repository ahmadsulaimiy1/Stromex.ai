"use client";

import { useEffect, useState } from "react";

import { Composer } from "@/components/chat/Composer";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { RequireAuth } from "@/components/layout/RequireAuth";
import { Button } from "@/components/ui/Button";
import { api } from "@/lib/api";
import type { ChatResponse, ConversationMode, ConversationRead, MessageRead } from "@/lib/types";

function ChatPage() {
  const [conversations, setConversations] = useState<ConversationRead[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageRead[]>([]);
  const [mode, setMode] = useState<ConversationMode>("general");
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadConversations() {
    const list = await api.get<ConversationRead[]>("/api/v1/conversations");
    setConversations(list);
  }

  useEffect(() => {
    void loadConversations();
  }, []);

  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    setLoadingMessages(true);
    api
      .get<MessageRead[]>(`/api/v1/conversations/${activeId}/messages`)
      .then(setMessages)
      .finally(() => setLoadingMessages(false));
  }, [activeId]);

  async function handleSend(message: string) {
    setError(null);
    const optimisticUser: MessageRead = {
      id: `pending-${Date.now()}`,
      role: "user",
      content: message,
      provider: null,
      model: null,
      routing_reason: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUser]);

    try {
      const response = await api.post<ChatResponse>("/api/v1/chat", {
        conversation_id: activeId,
        message,
        mode,
      });
      setMessages((prev) => [...prev, response.message]);
      if (!activeId) {
        setActiveId(response.conversation_id);
        void loadConversations();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message.");
    }
  }

  return (
    <div className="flex h-screen">
      <div className="flex w-64 shrink-0 flex-col border-r border-[color:var(--hairline)] p-3">
        <Button
          variant="secondary"
          className="mb-3 w-full"
          onClick={() => {
            setActiveId(null);
            setMessages([]);
          }}
        >
          + New conversation
        </Button>
        <div className="flex flex-col gap-1 overflow-y-auto">
          {conversations.map((conversation) => (
            <button
              key={conversation.id}
              onClick={() => setActiveId(conversation.id)}
              className={`truncate rounded-md px-3 py-2 text-left text-sm transition-colors ${
                activeId === conversation.id
                  ? "bg-[color:var(--bg-raised)] font-medium"
                  : "text-[color:var(--fg-muted)] hover:bg-[color:var(--bg-raised)]"
              }`}
            >
              {conversation.title}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-1 flex-col">
        <div className="flex-1 space-y-4 overflow-y-auto p-6">
          {loadingMessages && <p className="text-sm text-[color:var(--fg-muted)]">Loading…</p>}
          {!loadingMessages && messages.length === 0 && (
            <p className="text-sm text-[color:var(--fg-muted)]">
              Start a conversation — pick a mode below and ask anything.
            </p>
          )}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {error && <p className="text-sm text-rubrication">{error}</p>}
        </div>
        <Composer mode={mode} onModeChange={setMode} onSend={handleSend} />
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <RequireAuth>
      <ChatPage />
    </RequireAuth>
  );
}
