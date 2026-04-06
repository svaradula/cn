// src/App.jsx
import { useState } from "react";
import UploadSection from "./components/UploadSection";
import ShortlistPanel from "./components/ShortlistPanel";
import QuestionModal from "./components/QuestionModal";

export default function App() {
  const [jobDescription, setJobDescription] = useState("");
  const [shortlisted, setShortlisted] = useState([]);
  const [isScreening, setIsScreening] = useState(false);
  const [screenError, setScreenError] = useState(null);

  const [selectedResume, setSelectedResume] = useState(null);
  const [questionResults, setQuestionResults] = useState([]);
  const [candidateInfo, setCandidateInfo] = useState(null);   // ← new
  const [isGenerating, setIsGenerating] = useState(false);
  const [questionError, setQuestionError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

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
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/screen-resumes`, { method: "POST", body: form });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail ?? "Screening failed"); }
      const data = await res.json();
      setShortlisted(data.shortlisted);
    } catch (err) { setScreenError(err.message); }
    finally { setIsScreening(false); }
  };

  const handleGenerateQuestions = async (filename, levels) => {
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
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail ?? "Question generation failed"); }
      const data = await res.json();
      setQuestionResults(data.results);
      setCandidateInfo(data.candidate);    // ← new: {name, email, phone}
    } catch (err) { setQuestionError(err.message); }
    finally { setIsGenerating(false); }
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedResume(null);
    setQuestionResults([]);
    setCandidateInfo(null);
    setQuestionError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">

      {/* ── Header ── */}
      <header className="bg-white border-b border-gray-200 px-8 py-4 flex items-center gap-4 shadow-sm">
        <img
          src="https://cdn.prod.website-files.com/60c924f1b871a7316a4a5bb3/6234ecd8f1ef91e84c5ee437_UN%20Bordered_launch_2022.svg"
          alt="UN Logo"
          className="h-10 w-10 object-contain"
          onError={(e) => { e.target.style.display = "none"; e.target.nextSibling.style.display = "flex"; }}
        />
        <div style={{ display: "none" }} className="h-10 w-10 rounded-lg items-center justify-center">
          <div className="h-10 w-10 rounded-lg flex items-center justify-center text-white font-bold text-sm"
            style={{ background: "linear-gradient(135deg, #1B3A8C, #7B2391, #D91E7D)" }}>UN</div>
        </div>
        <div>
          <h1 className="text-base font-bold text-gray-900 leading-tight">Resume Screener</h1>
          <p className="text-xs text-gray-400">Powered by RAG · LangChain · GPT-4</p>
        </div>
        <div className="ml-auto">
          <span className="text-xs font-semibold text-white px-3 py-1.5 rounded-full"
            style={{ background: "linear-gradient(135deg, #1B3A8C, #7B2391, #D91E7D, #F05A28)" }}>
            AI Interview Assistant
          </span>
        </div>
      </header>

      <div className="h-1 w-full"
        style={{ background: "linear-gradient(90deg, #1B3A8C, #7B2391, #D91E7D, #F05A28)" }} />

      {/* ── Main ── */}
      <main className="max-w-6xl mx-auto px-6 py-10 grid grid-cols-1 lg:grid-cols-2 gap-8">
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
          />
        </section>
      </main>

      {modalOpen && (
        <QuestionModal
          filename={selectedResume}
          candidate={candidateInfo}           // ← passed down
          results={questionResults}
          isLoading={isGenerating}
          error={questionError}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
}

function PhaseLabel({ number, label }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <span className="text-xs font-bold tracking-widest px-2 py-0.5 rounded text-white"
        style={{ background: "linear-gradient(135deg, #7B2391, #D91E7D)" }}>
        PHASE {number}
      </span>
      <div className="flex-1 h-px bg-gray-200" />
      <span className="text-gray-400 text-xs">{label}</span>
    </div>
  );
}