// src/components/QuestionModal.jsx
import { useEffect, useRef, useState } from "react";

const BRAND = {
  navy: "#1B3A8C",
  purple: "#7B2391",
  pink: "#D91E7D",
  orange: "#F05A28",
};

const LEVEL_CONFIG = {
  basic: {
    label: "Basic",
    description: "Definitions · Syntax · Concepts",
    gradient: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple})`,
    headerColor: BRAND.navy,
    sectionBorder: "#dbeafe",
    sectionBg: "#eff6ff",
    badgeStyle: { background: "#dbeafe", color: BRAND.navy, border: "1px solid #bfdbfe" },
    indexStyle: { background: "#eff6ff", color: BRAND.navy, border: "1px solid #bfdbfe" },
    tagJD: { background: "#ede8fd", color: BRAND.purple, border: "1px solid #c4b0f0" },
    tagResume: { background: "#fde8f0", color: BRAND.pink, border: "1px solid #f4b8d4" },
    answerBg: "#f0f7ff", answerBorder: "#bfdbfe",
    toggleColor: BRAND.navy,
  },
  intermediate: {
    label: "Intermediate",
    description: "Scenarios · Trade-offs · Debugging",
    gradient: `linear-gradient(135deg, ${BRAND.purple}, ${BRAND.pink})`,
    headerColor: BRAND.purple,
    sectionBorder: "#ede8fd",
    sectionBg: "#f9f5ff",
    badgeStyle: { background: "#ede8fd", color: BRAND.purple, border: "1px solid #c4b0f0" },
    indexStyle: { background: "#f9f5ff", color: BRAND.purple, border: "1px solid #c4b0f0" },
    tagJD: { background: "#ede8fd", color: BRAND.purple, border: "1px solid #c4b0f0" },
    tagResume: { background: "#fde8f0", color: BRAND.pink, border: "1px solid #f4b8d4" },
    answerBg: "#faf5ff", answerBorder: "#c4b0f0",
    toggleColor: BRAND.purple,
  },
  advanced: {
    label: "Advanced",
    description: "Architecture · Scale · Optimisation",
    gradient: `linear-gradient(135deg, ${BRAND.pink}, ${BRAND.orange})`,
    headerColor: BRAND.pink,
    sectionBorder: "#fde8f0",
    sectionBg: "#fff5f9",
    badgeStyle: { background: "#fde8f0", color: BRAND.pink, border: "1px solid #f4b8d4" },
    indexStyle: { background: "#fff5f9", color: BRAND.pink, border: "1px solid #f4b8d4" },
    tagJD: { background: "#fde8f0", color: BRAND.pink, border: "1px solid #f4b8d4" },
    tagResume: { background: "#fef0e8", color: BRAND.orange, border: "1px solid #f4c9a8" },
    answerBg: "#fff8f5", answerBorder: "#f4c9a8",
    toggleColor: BRAND.pink,
  },
};

export default function QuestionModal({
  filename,
  candidate,    // { name, email, phone } | null
  results,
  isLoading,
  error,
  onClose,
}) {
  const overlayRef = useRef(null);

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const totalQuestions = results.reduce((s, r) => s + (r.items?.length ?? 0), 0);

  return (
    <div
      ref={overlayRef}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
      className="fixed inset-0 z-50 flex items-center justify-center px-4 py-8"
      style={{ background: "rgba(27,58,140,0.15)", backdropFilter: "blur(4px)" }}
    >
      <div
        className="relative w-full max-w-2xl h-[90vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden"
        style={{ background: "white", border: "1px solid #e5e7eb" }}
      >
        {/* Gradient top bar */}
        <div className="h-1 w-full shrink-0"
          style={{ background: `linear-gradient(90deg, ${BRAND.navy}, ${BRAND.purple}, ${BRAND.pink}, ${BRAND.orange})` }} />

        {/* ── Header ── */}
        <div className="flex items-start justify-between gap-4 px-6 py-4 border-b border-gray-100 shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold tracking-widest text-white px-2 py-0.5 rounded"
                style={{ background: `linear-gradient(135deg, ${BRAND.purple}, ${BRAND.pink})` }}>
                PHASE 03
              </span>
              <span className="text-xs text-gray-400">· 65% JD · 35% Resume</span>
            </div>
            <h2 className="text-base font-bold text-gray-900">Interview Questions</h2>
            <p className="text-xs text-gray-400 mt-0.5 truncate max-w-xs">{filename}</p>
          </div>
          <button onClick={onClose}
            className="text-gray-400 hover:text-gray-700 transition-colors text-2xl leading-none mt-0.5 shrink-0">
            ×
          </button>
        </div>

        {/* ── Candidate Info Card ── */}
        {/* Shows skeleton while loading, real data once available */}
        <div className="mx-6 mt-4 shrink-0">
          {isLoading || !candidate ? (
            // Skeleton loader
            <div className="rounded-xl p-4 flex items-center gap-4 animate-pulse"
              style={{ background: "#f9f5ff", border: "1px solid #ede8fd" }}>
              <div className="w-10 h-10 rounded-full bg-purple-200 shrink-0" />
              <div className="flex-1 flex flex-col gap-2">
                <div className="h-3 bg-purple-200 rounded w-36" />
                <div className="h-2.5 bg-purple-100 rounded w-48" />
                <div className="h-2.5 bg-purple-100 rounded w-40" />
              </div>
            </div>
          ) : (
            <CandidateCard candidate={candidate} />
          )}
        </div>

        {/* ── Recruiter hint ── */}
        {/* {!isLoading && totalQuestions > 0 && (
          <div className="mx-6 mt-3 px-4 py-2.5 rounded-lg flex items-center gap-3 shrink-0"
            style={{ background: "#f9f5ff", border: "1px solid #ede8fd" }}>
            <span className="text-base shrink-0">💡</span>
            <p className="text-xs text-gray-600 leading-relaxed">
              Click <span className="font-semibold" style={{ color: BRAND.purple }}>Show Answer</span> on
              any question to see a recruiter-friendly guide on what a good response sounds like.
            </p>
          </div>
        )} */}

        {/* ── Scrollable body ── */}
        <div className="flex-1 min-h-0 overflow-y-auto px-6 py-5 flex flex-col gap-4">

          {/* Loading spinner */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center gap-4 py-12">
              <div className="relative">
                <div className="w-12 h-12 rounded-full border-2 border-gray-200" />
                <div className="absolute inset-0 rounded-full border-2 border-t-transparent animate-spin"
                  style={{ borderColor: `${BRAND.purple} transparent transparent transparent` }} />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-gray-700">Generating questions & answers…</p>
                <p className="text-xs text-gray-400 mt-1">Applying 65% JD / 35% Resume weighting</p>
              </div>
            </div>
          )}

          {/* Error */}
          {!isLoading && error && (
            <div className="flex flex-col items-center gap-3 py-12 text-center">
              <div className="w-10 h-10 rounded-full bg-red-50 border border-red-200
                              flex items-center justify-center text-red-500 text-lg">!</div>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Accordion sections */}
          {!isLoading && !error && results.map((section, idx) => (
            <LevelSection key={section.level} section={section} defaultOpen={idx === 0} />
          ))}
        </div>

        {/* ── Footer ── */}
        {!isLoading && totalQuestions > 0 && (
          <div className="border-t border-gray-100 px-6 py-3 shrink-0
                          flex items-center justify-between bg-gray-50">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">
                {totalQuestions} questions · {results.length} level{results.length > 1 ? "s" : ""}
              </span>
              <span className="text-xs px-1.5 py-0.5 rounded border border-gray-200 text-gray-400">65% JD</span>
              <span className="text-xs px-1.5 py-0.5 rounded border border-gray-200 text-gray-400">35% Resume</span>
            </div>
            <button
              onClick={() => copyAll(results, candidate)}
              className="text-xs font-medium flex items-center gap-1.5 transition-opacity hover:opacity-70"
              style={{ color: BRAND.purple }}
            >
              <CopyIcon /> Copy all
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Candidate info card ───────────────────────────────────────────────────────

function CandidateCard({ candidate }) {
  const notFound = (v) => !v || v === "Not found";

  return (
    <div
      className="rounded-xl p-4 flex items-center gap-4"
      style={{ background: "#f9f5ff", border: "1px solid #ede8fd" }}
    >
      {/* Avatar with gradient initials */}
      <div
        className="w-11 h-11 rounded-full flex items-center justify-center
                   text-white font-bold text-sm shrink-0 select-none"
        style={{ background: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple}, ${BRAND.pink})` }}
      >
        {getInitials(candidate.name)}
      </div>

      {/* Details */}
      <div className="flex-1 min-w-0">
        {/* Name */}
        <p className="text-sm font-bold text-gray-900 truncate">
          {notFound(candidate.name)
            ? <span className="text-gray-400 font-normal italic">Name not found</span>
            : candidate.name
          }
        </p>

        {/* Email + Phone row */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1">
          <DetailChip
            icon={<EmailIcon />}
            value={candidate.email}
            href={notFound(candidate.email) ? null : `mailto:${candidate.email}`}
          />
          <DetailChip
            icon={<PhoneIcon />}
            value={candidate.phone}
            href={notFound(candidate.phone) ? null : `tel:${candidate.phone}`}
          />
        </div>
      </div>
    </div>
  );
}

function DetailChip({ icon, value, href }) {
  const notFound = !value || value === "Not found";
  const content = (
    <span className={`flex items-center gap-1.5 text-xs ${notFound ? "text-gray-400 italic" : "text-gray-600"}`}>
      <span className="shrink-0" style={{ color: BRAND.purple }}>{icon}</span>
      {notFound ? "Not found" : value}
    </span>
  );
  if (href) {
    return (
      <a href={href}
        className="flex items-center gap-1.5 text-xs transition-opacity hover:opacity-70"
        style={{ color: BRAND.purple }}
        onClick={(e) => e.stopPropagation()}>
        <span className="shrink-0">{icon}</span>
        {value}
      </a>
    );
  }
  return content;
}

// ── Level accordion ───────────────────────────────────────────────────────────

function LevelSection({ section, defaultOpen }) {
  const config = LEVEL_CONFIG[section.level] ?? LEVEL_CONFIG.basic;
  const [open, setOpen] = useState(defaultOpen ?? true);

  return (
    <div className="rounded-xl"
      style={{ border: `1px solid ${config.sectionBorder}` }}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 transition-all cursor-pointer"
        style={{ background: config.sectionBg }}
      >
        <div className="flex items-center gap-3">
          <svg className="w-3.5 h-3.5 transition-transform duration-200"
            style={{ color: config.headerColor, transform: open ? "rotate(180deg)" : "rotate(0deg)" }}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
          <span className="text-sm font-bold text-white px-2.5 py-0.5 rounded-full"
            style={{ background: config.gradient }}>
            {config.label}
          </span>
          <span className="text-xs text-gray-400 hidden sm:inline">{config.description}</span>
        </div>
        <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={config.badgeStyle}>
          {section.items.length} questions
        </span>
      </button>

      {open && (
        <ol className="flex flex-col divide-y divide-gray-100 bg-white">
          {section.items.map((item, i) => (
            <QuestionItem key={i} index={i + 1} item={item} config={config} />
          ))}
        </ol>
      )}
    </div>
  );
}

// ── Question + answer item ────────────────────────────────────────────────────

function QuestionItem({ index, item, config }) {
  const [answerOpen, setAnswerOpen] = useState(false);
  const isJD = item.question.includes("[JD-Focused]");
  const isResume = item.question.includes("[Resume-Focused]");
  const cleanQuestion = item.question.replace("[JD-Focused]", "").replace("[Resume-Focused]", "").trim();
  const hasAnswer = item.answer?.trim().length > 0;

  return (
    <li className="px-4 py-4 flex flex-col gap-2">
      <div className="flex gap-3">
        <div className="shrink-0 w-6 h-6 rounded-full border flex items-center
                        justify-center text-xs font-bold mt-0.5"
          style={config.indexStyle}>
          {index}
        </div>
        <div className="flex-1 flex flex-col gap-1.5">
          {(isJD || isResume) && (
            <span className="self-start text-xs font-semibold px-2 py-0.5 rounded-full border"
              style={isJD ? config.tagJD : config.tagResume}>
              {isJD ? "JD-Focused" : "Resume-Focused"}
            </span>
          )}
          <p className="text-sm text-gray-800 leading-relaxed">{cleanQuestion}</p>
          {hasAnswer && (
            <button
              onClick={() => setAnswerOpen((o) => !o)}
              className="self-start flex items-center gap-1.5 text-xs font-semibold mt-1 transition-opacity hover:opacity-70"
              style={{ color: config.toggleColor }}
            >
              <ChevronIcon open={answerOpen} />
              {answerOpen ? "Hide Answer" : "Show Answer"}
            </button>
          )}
        </div>
      </div>

      {hasAnswer && answerOpen && (
        <div className="ml-9 rounded-lg px-4 py-3"
          style={{ background: config.answerBg, border: `1px solid ${config.answerBorder}` }}>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-bold text-gray-500 tracking-wider uppercase">Recruiter Guide</span>
            <span className="text-xs text-gray-400">· what to listen for</span>
          </div>
          <p className="text-xs text-gray-700 leading-relaxed">{item.answer}</p>
        </div>
      )}
    </li>
  );
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function getInitials(name) {
  if (!name || name === "Not found") return "?";
  return name.trim().split(/\s+/).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
}

function copyAll(results, candidate) {
  const header = candidate
    ? `Candidate: ${candidate.name}\nEmail: ${candidate.email}\nPhone: ${candidate.phone}\n`
    : "";
  const lines = results.flatMap((section) => {
    const h = `\n## ${section.level.toUpperCase()} QUESTIONS\n`;
    const qs = section.items.map((item, i) =>
      `${i + 1}. ${item.question}\n   ANSWER: ${item.answer}`
    ).join("\n\n");
    return [h, qs];
  });
  navigator.clipboard.writeText(header + lines.join("\n")).catch(console.error);
}

function ChevronIcon({ open }) {
  return (
    <svg className="w-3 h-3 transition-transform duration-200"
      style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)" }}
      fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

function CopyIcon() {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2
           m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  );
}

function EmailIcon() {
  return (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}

function PhoneIcon() {
  return (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13
           a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2
           2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
    </svg>
  );
}