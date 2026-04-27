/**
 * App.jsx — Root component with tab navigation and error boundary.
 */
import { useState, Component } from "react";
import { LayoutDashboard, MessageCircle, Search, ShieldCheck, AlertTriangle } from "lucide-react";
import Dashboard from "./components/Dashboard";
import AdvisorChat from "./components/AdvisorChat";
import FundExplorer from "./components/FundExplorer";
import RiskProfiler from "./components/RiskProfiler";

// ── Error Boundary — catches any render crash and shows a readable message ───
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-center px-6">
          <AlertTriangle size={32} className="text-amber-400 mb-3" />
          <p className="font-semibold text-gray-800 mb-1">Something went wrong</p>
          <p className="text-sm text-gray-500 mb-4">{this.state.error.message}</p>
          <button
            onClick={() => this.setState({ error: null })}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── Tabs ─────────────────────────────────────────────────────────────────────
const TABS = [
  { id: "chat",      label: "Advisor",  icon: MessageCircle   },
  { id: "dashboard", label: "Budget",   icon: LayoutDashboard },
  { id: "funds",     label: "Funds",    icon: Search          },
  { id: "profile",   label: "Profile",  icon: ShieldCheck     },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [userId, setUserId]       = useState(null);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">

      {/* ── Top nav ── */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">

          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-600 to-blue-700
                            flex items-center justify-center text-white font-bold text-sm shadow">
              ₹
            </div>
            <div>
              <p className="font-bold text-gray-900 text-sm leading-none">MF Advisor AI</p>
              <p className="text-xs text-gray-400 leading-none mt-0.5">
                GPT-4o + Pinecone RAG
              </p>
            </div>
          </div>

          {/* Desktop tabs */}
          <nav className="hidden sm:flex gap-1">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm
                            font-medium transition-all
                  ${activeTab === id
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"}`}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* ── Page content ── */}
      <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-5">
        <ErrorBoundary key={activeTab}>
          {activeTab === "chat" && (
            <div className="h-[calc(100vh-130px)] rounded-2xl overflow-hidden
                            border border-gray-100 shadow-sm bg-white">
              <AdvisorChat userId={userId} />
            </div>
          )}
          {activeTab === "dashboard" && <Dashboard userId={userId} />}
          {activeTab === "funds"     && <FundExplorer />}
          {activeTab === "profile"   && (
            <RiskProfiler onProfileSaved={(p) => setUserId(p.user_id)} />
          )}
        </ErrorBoundary>
      </main>

      {/* ── Mobile bottom bar ── */}
      <nav className="sm:hidden fixed bottom-0 left-0 right-0 bg-white border-t
                      border-gray-100 flex shadow-lg z-10">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex-1 flex flex-col items-center gap-1 py-2.5 text-xs
                        font-medium transition-colors
              ${activeTab === id ? "text-blue-600" : "text-gray-400"}`}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>
    </div>
  );
}