// src/App.jsx
import { useEffect, useState } from "react";
import UploadSection from "./components/UploadSection";
import ShortlistPanel from "./components/ShortlistPanel";
import QuestionModal from "./components/QuestionModal";
import SelectedCandidates from "./components/SelectedCandidates";
import ScheduleModal from "./components/ScheduleModal";
import ScheduledCandidates from "./components/ScheduledCandidates";

const BRAND = { navy: "#1B3A8C", purple: "#7B2391", pink: "#D91E7D", orange: "#F05A28" };

export default function App() {
  const [jobDescription, setJobDescription] = useState("");

  // Phase 2 — screened results
  const [shortlisted, setShortlisted] = useState([]);
  const [isScreening, setIsScreening] = useState(false);
  const [screenError, setScreenError] = useState(null);

  // Phase 3 — question modal
  const [selectedResume, setSelectedResume]     = useState(null);
  const [selectedScore, setSelectedScore]       = useState(null);
  const [questionResults, setQuestionResults]   = useState([]);
  const [candidateInfo, setCandidateInfo]       = useState(null);
  const [isGenerating, setIsGenerating]         = useState(false);
  const [questionError, setQuestionError]       = useState(null);
  const [modalOpen, setModalOpen]               = useState(false);

  // Phase 4 — shortlisted for interview
  // { filename, info: {name, email, phone}, score }
  const [selectedCandidates, setSelectedCandidates] = useState([]);

  // Phase 5 — scheduled interviews
  // { candidate: {...}, schedule: {date, time, timezone, subject, teamsLink, calendarLink} }
  const [scheduledCandidates, setScheduledCandidates] = useState([]);

  // Schedule modal
  const [scheduleTarget, setScheduleTarget]   = useState(null);  // candidate object
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);

  // HR user name (for email sign-off)
  const [hrEmail] = useState("");

  // Toast
  const [toast, setToast] = useState(null);  // { message, type: "success"|"error" }



  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // ── Extract role name from first line of JD ───────────────────────────────
  const roleName = jobDescription.trim().split("\n")[0].slice(0, 80) || "the role";

  // ── Phase 1: Screen ────────────────────────────────────────────────────────
  const handleScreen = async (files, threshold = 0.65) => {
    setIsScreening(true);
    setScreenError(null);
    setShortlisted([]);
    const form = new FormData();
    form.append("job_description", jobDescription);
    form.append("top_k", "3");
    form.append("threshold", threshold.toString());
    files.forEach((f) => form.append("resumes", f));
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/screen-resumes`,
        { method: "POST", body: form });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail ?? "Screening failed"); }
      const data = await res.json();
      setShortlisted(data.shortlisted);
    } catch (err) { setScreenError(err.message); }
    finally { setIsScreening(false); }
  };

  // ── Phase 3: Generate questions ────────────────────────────────────────────
  const handleGenerateQuestions = async (filename, levels) => {
    const match = shortlisted.find((r) => r.filename === filename);
    setSelectedScore(match?.score ?? null);
    setSelectedResume(filename);
    setQuestionResults([]);
    setCandidateInfo(null);
    setQuestionError(null);
    setIsGenerating(true);
    setModalOpen(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/generate-questions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename, job_description: jobDescription, levels }),
      });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail ?? "Failed"); }
      const data = await res.json();
      setQuestionResults(data.results);
      setCandidateInfo(data.candidate);
    } catch (err) { setQuestionError(err.message); }
    finally { setIsGenerating(false); }
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedResume(null);
    setSelectedScore(null);
    setQuestionResults([]);
    setCandidateInfo(null);
    setQuestionError(null);
  };

  // ── Phase 2: Direct schedule (skip Phase 3) ──────────────────────────────
  // Fetches candidate contact info first, then opens the schedule modal
  const handleDirectSchedule = async (filename, score) => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/extract-candidate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename }),
      });
      if (!res.ok) throw new Error("Could not fetch candidate info");
      const info = await res.json();
      // Open schedule modal directly with extracted info
      setScheduleTarget({ filename, info, score });
      setScheduleModalOpen(true);
    } catch (err) {
      // Fallback: open modal with empty info — recruiter fills manually
      setScheduleTarget({
        filename,
        info: { name: "Not found", email: "Not found", phone: "Not found" },
        score,
      });
      setScheduleModalOpen(true);
    }
  };

  // ── Phase 4: Shortlist candidate (from Phase 3 modal) ─────────────────────
  // When shortlisted → add to Phase 4 AND remove from Phase 2
  const handleShortlist = (filename, candidate, score) => {
    if (candidate) {
      // Add to Phase 4 (no duplicates)
      setSelectedCandidates((prev) => {
        if (prev.find((c) => c.filename === filename)) return prev;
        return [...prev, { filename, info: candidate, score }];
      });
      // Remove from Phase 2 shortlist
      setShortlisted((prev) => prev.filter((r) => r.filename !== filename));
    } else {
      // Un-shortlist: remove from Phase 4, restore to Phase 2
      setSelectedCandidates((prev) => prev.filter((c) => c.filename !== filename));
    }
  };

  const handleRemoveCandidate = (filename) => {
    setSelectedCandidates((prev) => prev.filter((c) => c.filename !== filename));
  };

  const isShortlisted = (filename) => selectedCandidates.some((c) => c.filename === filename);

  // ── Phase 5: Open schedule modal ──────────────────────────────────────────
  const handleOpenSchedule = (candidate) => {
    setScheduleTarget(candidate);
    setScheduleModalOpen(true);
  };

  // ── Phase 5: Confirm schedule — move Phase 4 → Phase 5 ───────────────────
  const handleScheduled = (candidate, scheduleDetails) => {
    // Move to Phase 5
    setScheduledCandidates((prev) => {
      const exists = prev.find((e) => e.candidate.filename === candidate.filename);
      if (exists) return prev;
      return [...prev, { candidate, schedule: scheduleDetails }];
    });
    // Remove from Phase 4 (shortlist → schedule flow)
    setSelectedCandidates((prev) => prev.filter((c) => c.filename !== candidate.filename));
    // Remove from Phase 2 (direct schedule from shortlist panel)
    setShortlisted((prev) => prev.filter((r) => r.filename !== candidate.filename));
    // Close schedule modal
    setScheduleModalOpen(false);
    setScheduleTarget(null);
    showToast("Interview scheduled successfully ✓", "success");
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">

      {/* ── Toast notification ── */}
      {toast && (
        <div
          className="fixed top-5 right-5 z-[100] flex items-center gap-3 px-5 py-3
                     rounded-xl shadow-lg text-sm font-medium text-white
                     transition-all duration-300"
          style={{
            background: toast.type === "success"
              ? "linear-gradient(135deg, #16a34a, #15803d)"
              : "linear-gradient(135deg, #dc2626, #b91c1c)",
          }}
        >
          {toast.type === "success" ? "✓" : "✗"} {toast.message}
        </div>
      )}

      {/* ── Header ── */}
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center gap-4 shadow-sm">
        <img
          src="https://cdn.prod.website-files.com/60c924f1b871a7316a4a5bb3/6234ecd8f1ef91e84c5ee437_UN%20Bordered_launch_2022.svg"
          alt="UN Logo" className="h-10 w-10 object-contain"
          onError={(e) => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }}
        />
        <div style={{ display: "none" }}>
          <div className="h-10 w-10 rounded-lg flex items-center justify-center text-white font-bold text-sm"
               style={{ background: "linear-gradient(135deg, #1B3A8C, #7B2391, #D91E7D)" }}>UN</div>
        </div>
        <div>
          <h1 className="text-base font-bold text-gray-900 leading-tight">Resume Screener</h1>
          <p className="text-xs text-gray-400">Powered by RAG · LangChain · GPT-4</p>
        </div>

        <div className="ml-auto flex items-center gap-3">
          {/* Scheduled count badge */}
          {scheduledCandidates.length > 0 && (
            <span className="text-xs font-bold text-white px-3 py-1.5 rounded-full flex items-center gap-1.5"
                  style={{ background: "linear-gradient(135deg, #16a34a, #15803d)" }}>
              📅 {scheduledCandidates.length} scheduled
            </span>
          )}
          {/* Shortlisted count badge */}
          {selectedCandidates.length > 0 && (
            <span className="text-xs font-bold text-white px-3 py-1.5 rounded-full flex items-center gap-1.5"
                  style={{ background: `linear-gradient(135deg, ${BRAND.purple}, ${BRAND.pink})` }}>
              ★ {selectedCandidates.length} shortlisted
            </span>
          )}

          <span className="text-xs font-semibold text-white px-3 py-1.5 rounded-full"
                style={{ background: "linear-gradient(135deg, #1B3A8C, #7B2391, #D91E7D, #F05A28)" }}>
            AI Interview Assistant
          </span>
        </div>
      </header>

      <div className="h-1 w-full"
           style={{ background: "linear-gradient(90deg, #1B3A8C, #7B2391, #D91E7D, #F05A28)" }} />

      {/* ── Main layout ── */}
      <main className="max-w-6xl mx-auto px-6 py-10 flex flex-col gap-10">

        {/* Phase 1 + 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section>
            <PhaseLabel number="01" label="Upload & Screen" />
            <UploadSection
              jobDescription={jobDescription}
              onJDChange={setJobDescription}
              onScreen={handleScreen}
              isLoading={isScreening}
              error={screenError}
            />
          </section>
          <section>
            <PhaseLabel number="02" label="Shortlisted Candidates" />
            <ShortlistPanel
              results={shortlisted}
              isLoading={isScreening}
              onSelect={handleGenerateQuestions}
              onSchedule={handleDirectSchedule}
            />
          </section>
        </div>

        <hr className="border-gray-200" />

        {/* Phase 4 + 5 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section>
            <PhaseLabel number="04" label="Ready for Interview Schedule" accent="#16a34a" />
            <SelectedCandidates
              candidates={selectedCandidates}
              onRemove={handleRemoveCandidate}
              onSchedule={handleOpenSchedule}
            />
          </section>
          <section>
            <PhaseLabel number="05" label="Interview Scheduled" accent="#1d4ed8" />
            <ScheduledCandidates candidates={scheduledCandidates} />
          </section>
        </div>
      </main>

      {/* Phase 3 modal */}
      {modalOpen && (
        <QuestionModal
          filename={selectedResume}
          candidate={candidateInfo}
          results={questionResults}
          isLoading={isGenerating}
          error={questionError}
          score={selectedScore}
          onClose={handleCloseModal}
          onShortlist={handleShortlist}
          isShortlisted={isShortlisted(selectedResume)}
        />
      )}

      {/* Schedule modal */}
      {scheduleModalOpen && scheduleTarget && (
        <ScheduleModal
          candidate={scheduleTarget}
          roleName={roleName}
          hrEmail={hrEmail}
          onClose={() => { setScheduleModalOpen(false); setScheduleTarget(null); }}
          onScheduled={handleScheduled}
        />
      )}
    </div>
  );
}

function PhaseLabel({ number, label, accent }) {
  const bg = accent
    ? `linear-gradient(135deg, ${accent}, ${accent}cc)`
    : "linear-gradient(135deg, #7B2391, #D91E7D)";
  return (
    <div className="flex items-center gap-3 mb-5">
      <span className="text-xs font-bold tracking-widest px-2 py-0.5 rounded text-white"
            style={{ background: bg }}>
        PHASE {number}
      </span>
      <div className="flex-1 h-px bg-gray-200" />
      <span className="text-gray-400 text-xs">{label}</span>
    </div>
  );
}