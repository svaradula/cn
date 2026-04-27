/**
 * useChat.js - WebSocket streaming chat hook.
 *
 * Connects to ws://127.0.0.1:8000/ws/chat via Vite proxy.
 * Streams token-by-token responses from GPT-4o.
 * Auto-reconnects up to 5 times on disconnect.
 */
import { useState, useRef, useEffect, useCallback } from "react";

const WS_URL = "ws://localhost:8000/ws/chat";
const MAX_RECONNECT = 5;
const RECONNECT_DELAY = 2000;

export function useChat(userId) {
  const [messages, setMessages]       = useState([]);
  const [isStreaming, setIsStreaming]  = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError]             = useState(null);

  const wsRef             = useRef(null);
  const reconnectCount    = useRef(0);
  const reconnectTimer    = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        reconnectCount.current = 0;
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsStreaming(false);
        if (reconnectCount.current < MAX_RECONNECT) {
          const delay = RECONNECT_DELAY * (reconnectCount.current + 1);
          reconnectTimer.current = setTimeout(() => {
            reconnectCount.current += 1;
            connect();
          }, delay);
        }
      };

      ws.onerror = () => {
        setError("Cannot connect to backend. Is uvicorn running on port 8000?");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === "token") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                return [
                  ...updated.slice(0, -1),
                  { ...last, content: last.content + data.token },
                ];
              }
              return updated;
            });
          } else if (data.type === "sources") {
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                return [
                  ...updated.slice(0, -1),
                  { ...last, sources: data.sources },
                ];
              }
              return updated;
            });
          } else if (data.type === "done") {
            setIsStreaming(false);
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant") {
                return [...updated.slice(0, -1), { ...last, streaming: false }];
              }
              return updated;
            });
          } else if (data.type === "error") {
            setIsStreaming(false);
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last && last.role === "assistant" && last.streaming) {
                return [
                  ...updated.slice(0, -1),
                  { ...last, content: "Error: " + data.message, streaming: false, isError: true },
                ];
              }
              return updated;
            });
          }
        } catch (e) {
          console.error("WebSocket message parse error:", e);
        }
      };
    } catch (e) {
      setError("WebSocket not supported or blocked.");
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const sendMessage = useCallback(
    (text) => {
      const trimmed = (text || "").trim();
      if (!trimmed || isStreaming || !isConnected) return;

      const userMsg = {
        id: Date.now(),
        role: "user",
        content: trimmed,
      };
      const assistantMsg = {
        id: Date.now() + 1,
        role: "assistant",
        content: "",
        streaming: true,
        sources: [],
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);
      setError(null);

      const history = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      wsRef.current.send(
        JSON.stringify({
          user_id: userId || "anonymous",
          query: trimmed,
          chat_history: history,
        })
      );
    },
    [isStreaming, isConnected, messages, userId]
  );

  const clearMessages = useCallback(() => setMessages([]), []);

  return { messages, isStreaming, isConnected, error, sendMessage, clearMessages };
}