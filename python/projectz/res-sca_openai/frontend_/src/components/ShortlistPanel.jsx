// src/components/ShortlistPanel.jsx
import { useState } from "react";

const LEVELS = [
  { id: "basic", label: "Basic", description: "Definitions · Syntax · Concepts", gradient: "linear-gradient(135deg,#1B3A8C,#7B2391)" },
  { id: "intermediate", label: "Intermediate", description: "Scenarios · Trade-offs · Debugging", gradient: "linear-gradient(135deg,#7B2391,#D91E7D)" },
  { id: "advanced", label: "Advanced", description: "Architecture · Optimisation · Scale", gradient: "linear-gradient(135deg,#D91E7D,#F05A28)" },
];

export default function ShortlistPanel({ results, isLoading, onSelect }) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-48 bg-gray-100 rounded-xl border border-gray-200 animate-pulse" />
        ))}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64
                      border-2 border-dashed border-gray-200 rounded-xl text-gray-400">
        <EmptyIcon />
        <p className="mt-3 text-sm">Shortlisted candidates will appear here</p>
        <p className="text-xs mt-1 text-gray-300">Upload resumes and run screening first</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      {results.map((candidate, idx) => (
        <CandidateCard key={candidate.filename} rank={idx + 1} candidate={candidate} onSelect={onSelect} />
      ))}
    </div>
  );
}

function CandidateCard({ rank, candidate, onSelect }) {
  const { filename, score } = candidate;
  const pct = Math.round(score * 100);
  const [selectedLevels, setSelectedLevels] = useState({ basic: true, intermediate: false, advanced: false });

  const toggleLevel = (id) => setSelectedLevels((prev) => ({ ...prev, [id]: !prev[id] }));

  const activeLevels = Object.entries(selectedLevels).filter(([, v]) => v).map(([k]) => k);
  const levelsToSend = activeLevels.length > 0 ? activeLevels : ["basic"];
  const totalQuestions = levelsToSend.length * 5;

  // Score bar gradient based on strength
  const barGradient =
    pct >= 70 ? "linear-gradient(90deg,#1B3A8C,#7B2391,#D91E7D)" :
      pct >= 50 ? "linear-gradient(90deg,#7B2391,#D91E7D)" :
        "linear-gradient(90deg,#D91E7D,#F05A28)";

  const badgeStyle =
    pct >= 70 ? { background: "#ede8fd", color: "#7B2391", border: "1px solid #c4b0f0" } :
      pct >= 50 ? { background: "#fde8f0", color: "#D91E7D", border: "1px solid #f4b8d4" } :
        { background: "#fef0e8", color: "#F05A28", border: "1px solid #f4c9a8" };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm
                    hover:shadow-md hover:border-gray-300 transition-all">

      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-3 min-w-0">
          {/* Rank bubble with gradient */}
          <div
            className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center
                       text-xs font-bold text-white"
            style={{ background: "linear-gradient(135deg,#1B3A8C,#7B2391)" }}
          >
            {rank}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-800 truncate">
              {filename.replace(/\.[^/.]+$/, "")}
            </p>
            <p className="text-xs text-gray-400 truncate">{filename}</p>
          </div>
        </div>
        <span className="text-xs font-bold px-2.5 py-1 rounded-full shrink-0"
          style={badgeStyle}>
          {pct}% match
        </span>
      </div>

      {/* Score bar */}
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden mb-4">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: barGradient }}
        />
      </div>

      {/* Difficulty checkboxes */}
      <div className="mb-4">
        <p className="text-xs font-semibold text-gray-400 mb-2 tracking-wider uppercase">
          Question Difficulty
        </p>
        <div className="flex flex-col gap-2">
          {LEVELS.map((level) => (
            <DifficultyCheckbox
              key={level.id}
              level={level}
              checked={selectedLevels[level.id]}
              onChange={() => toggleLevel(level.id)}
            />
          ))}
        </div>
        {activeLevels.length === 0 && (
          <p className="text-xs text-gray-400 mt-2 italic">
            No level selected — defaults to Basic (5 questions)
          </p>
        )}
      </div>

      {/* Generate button */}
      <button
        onClick={() => onSelect(filename, levelsToSend)}
        className="w-full py-2.5 rounded-lg text-xs font-bold tracking-wide
                   text-white transition-all duration-200 flex items-center justify-center gap-2"
        style={{
          background: "linear-gradient(135deg, #1B3A8C, #7B2391, #D91E7D)",
          boxShadow: "0 4px 12px rgba(123,35,145,0.25)",
        }}
        onMouseOver={(e) => e.currentTarget.style.opacity = "0.9"}
        onMouseOut={(e) => e.currentTarget.style.opacity = "1"}
      >
        Generate {totalQuestions} Interview Question{totalQuestions !== 1 ? "s" : ""}
        <span className="opacity-70">→</span>
      </button>
    </div>
  );
}

function DifficultyCheckbox({ level, checked, onChange }) {
  return (
    <label
      className="flex items-center gap-3 px-3 py-2.5 rounded-lg border cursor-pointer
                 transition-all select-none"
      style={{
        borderColor: checked ? "transparent" : "#e5e7eb",
        background: checked ? "transparent" : "#fafafa",
        backgroundImage: checked ? `${level.gradient}15` : "none",
        outline: checked ? `1.5px solid` : "none",
        outlineColor: checked ? "#7B2391" : "transparent",
      }}
    >
      {/* Custom checkbox */}
      <div
        className="w-4 h-4 rounded flex items-center justify-center shrink-0 border transition-all"
        style={{
          background: checked ? level.gradient : "white",
          borderColor: checked ? "transparent" : "#d1d5db",
        }}
      >
        {checked && (
          <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24"
            stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        )}
      </div>

      <input type="checkbox" className="sr-only" checked={checked} onChange={onChange} />

      <div className="flex-1 flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-700">{level.label}</span>
        <span className="text-xs text-gray-400">{level.description}</span>
      </div>

      {checked && (
        <span
          className="text-xs font-bold px-1.5 py-0.5 rounded text-white shrink-0"
          style={{ background: level.gradient }}
        >
          5 Qs
        </span>
      )}
    </label>
  );
}

function EmptyIcon() {
  return (
    <svg className="w-10 h-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586
           a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}