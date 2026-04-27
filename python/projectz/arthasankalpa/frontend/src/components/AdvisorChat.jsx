/**
 * AdvisorChat.jsx - Streaming chat UI connected via WebSocket.
 */
import { useState, useRef, useEffect } from "react";
import { Send, Wifi, WifiOff, RefreshCw, Bot, User, TrendingUp, AlertCircle } from "lucide-react";
import { useChat } from "../hooks/useChat";

const PROMPTS = [
  "Show me top 5 ELSS funds for tax saving under 80C",
  "How should I invest Rs.15,000/month for 10 years?",
  "Which large-cap funds have highest 5-year CAGR?",
  "Difference between liquid and overnight funds",
  "Compare index funds vs active equity funds",
  "Good time to start SIP in mid-cap funds?",
];

function SourceCitation({ sources }) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <p className="text-xs text-gray-400 mb-2 font-medium">Sources:</p>
      <div className="flex flex-wrap gap-2">
        {sources.map((s, i) => (
          <span key={i} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded border border-blue-100">
            {(s.scheme_name || "").slice(0, 35)}
            {s.nav > 0 && <span className="ml-1 text-blue-400">Rs.{Number(s.nav).toFixed(2)}</span>}
          </span>
        ))}
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <div className="flex gap-1 items-center py-1">
      {[0, 150, 300].map((d) => (
        <span key={d} className="w-2 h-2 bg-gray-300 rounded-full animate-bounce"
          style={{ animationDelay: d + "ms" }} />
      ))}
    </div>
  );
}

function Bubble({ msg }) {
  const isUser = msg.role === "user";
  return (
    <div className={"flex gap-3 " + (isUser ? "flex-row-reverse" : "flex-row")}>
      <div className={"w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-white " +
        (isUser ? "bg-blue-600" : "bg-gradient-to-br from-emerald-500 to-teal-600")}>
        {isUser ? <User size={14} /> : <Bot size={14} />}
      </div>
      <div className={"max-w-3xl rounded-2xl px-4 py-3 text-sm leading-relaxed " +
        (isUser
          ? "bg-blue-600 text-white rounded-tr-sm"
          : "bg-white border border-gray-100 text-gray-800 rounded-tl-sm shadow-sm") +
        (msg.isError ? " bg-red-50 border-red-200 text-red-700" : "")}>
        {isUser
          ? <p>{msg.content}</p>
          : <>
              {msg.content ? <div className="whitespace-pre-wrap">{msg.content}</div> : <TypingDots />}
              {!msg.streaming && <SourceCitation sources={msg.sources} />}
            </>
        }
      </div>
    </div>
  );
}

export default function AdvisorChat({ userId }) {
  const [input, setInput] = useState("");
  const { messages, isStreaming, isConnected, error, sendMessage, clearMessages } = useChat(userId);
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = (text) => {
    const msg = (text || input).trim();
    if (!msg || isStreaming) return;
    sendMessage(msg);
    setInput("");
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">

      {/* Header */}
      <div className="bg-white border-b px-5 py-3 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
            <TrendingUp size={18} className="text-white" />
          </div>
          <div>
            <p className="font-semibold text-gray-900 text-sm">FinBot Advisor</p>
            <p className="text-xs text-gray-400">GPT-4o + Pinecone RAG</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className={"flex items-center gap-1.5 text-xs font-medium " +
            (isConnected ? "text-emerald-600" : "text-amber-500")}>
            {isConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
            {isConnected ? "Connected" : "Backend offline"}
          </span>
          {messages.length > 0 && (
            <button onClick={clearMessages} className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1">
              <RefreshCw size={11} /> Clear
            </button>
          )}
        </div>
      </div>

      {/* Offline banner */}
      {!isConnected && (
        <div className="px-4 py-2 bg-amber-50 border-b border-amber-100 text-xs text-amber-700 flex items-center gap-2 flex-shrink-0">
          <AlertCircle size={12} />
          <span>Start backend: <code className="font-mono bg-amber-100 px-1 rounded">uvicorn main:app --reload --port 8000</code></span>
        </div>
      )}

      {/* Disclaimer */}
      <div className="px-4 py-1.5 bg-amber-50 border-b border-amber-100 text-xs text-amber-700 flex-shrink-0">
        AI insights only - not SEBI-registered advice. Verify before investing.
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4 scrollbar-thin">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center py-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mb-4 shadow-lg">
              <TrendingUp size={32} className="text-white" />
            </div>
            <h3 className="font-semibold text-gray-800 mb-1">Your AI Financial Advisor</h3>
            <p className="text-sm text-gray-400 mb-6 max-w-sm">
              Ask about mutual funds, SIP planning, tax saving, or budget allocation.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
              {PROMPTS.map((p) => (
                <button key={p} onClick={() => send(p)} disabled={!isConnected}
                  className="text-left text-xs px-3 py-2.5 border border-gray-200 rounded-xl
                             hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700
                             transition-all disabled:opacity-40 text-gray-600 bg-white">
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => <Bubble key={m.id} msg={m} />)
        )}
        {error && (
          <div className="text-xs text-red-500 text-center py-2 bg-red-50 rounded-lg border border-red-100">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t px-4 py-3 flex-shrink-0">
        <div className="flex gap-2 items-end">
          <textarea ref={inputRef} value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
            disabled={isStreaming || !isConnected}
            placeholder={isConnected ? "Ask about funds, SIP, tax saving..." : "Start backend to chat..."}
            rows={1}
            style={{ minHeight: "42px", maxHeight: "120px" }}
            className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-2.5 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       disabled:bg-gray-50 disabled:text-gray-400 scrollbar-thin" />
          <button onClick={() => send()} disabled={isStreaming || !isConnected || !input.trim()}
            className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center
                       hover:bg-blue-700 disabled:opacity-40 transition-all flex-shrink-0">
            {isStreaming
              ? <RefreshCw size={16} className="text-white animate-spin" />
              : <Send size={16} className="text-white" />}
          </button>
        </div>
        <p className="text-xs text-gray-300 mt-1.5 text-center">Enter to send - Shift+Enter for new line</p>
      </div>
    </div>
  );
}