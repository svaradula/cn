// src/components/UploadSection.jsx
import { useCallback, useRef, useState } from "react";

const ACCEPTED_MIME = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

// Threshold presets — shown as radio buttons so the recruiter understands the tradeoff
const THRESHOLD_PRESETS = [
  { value: 0.30, label: "Broad", description: "More results, some may be loosely relevant" },
  { value: 0.45, label: "Balanced", description: "Recommended — filters weak matches" },
  { value: 0.55, label: "Strict", description: "Fewer results, only strong matches" },
];

export default function UploadSection({ jobDescription, onJDChange, onScreen, isLoading, error }) {
  const [files, setFiles] = useState([]);
  const [dragging, setDragging] = useState(false);
  const [threshold, setThreshold] = useState(0.40);   // ← raised default from 0.30
  const fileInputRef = useRef(null);

  const addFiles = useCallback((incoming) => {
    const valid = Array.from(incoming).filter(
      (f) => ACCEPTED_MIME.includes(f.type) || f.name.endsWith(".pdf") || f.name.endsWith(".docx")
    );
    setFiles((prev) => {
      const names = new Set(prev.map((f) => f.name));
      return [...prev, ...valid.filter((f) => !names.has(f.name))];
    });
  }, []);

  const removeFile = (name) => setFiles((prev) => prev.filter((f) => f.name !== name));

  const onDrop = (e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); };

  const canSubmit = jobDescription.trim().length > 20 && files.length > 0 && !isLoading;

  return (
    <div className="flex flex-col gap-5">

      {/* JD textarea */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 mb-2 tracking-wider uppercase">
          Job Description
        </label>
        <textarea
          className="w-full h-44 bg-white border border-gray-300 rounded-xl px-4 py-3
                     text-sm text-gray-800 placeholder-gray-400 resize-none
                     focus:outline-none transition-all"
          onFocus={(e) => e.target.style.borderColor = "#7B2391"}
          onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
          placeholder="Paste the full job description here…"
          value={jobDescription}
          onChange={(e) => onJDChange(e.target.value)}
        />
      </div>

      {/* Drop zone */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 mb-2 tracking-wider uppercase">
          Resume Files (PDF / DOCX)
        </label>
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className="flex flex-col items-center justify-center gap-2 rounded-xl p-8
                     cursor-pointer transition-all select-none border-2 border-dashed"
          style={{
            borderColor: dragging ? "#D91E7D" : "#d1d5db",
            background: dragging ? "#fdf2f8" : "#fafafa",
          }}
        >
          <UploadIcon dragging={dragging} />
          <p className="text-sm text-gray-500">
            Drop PDFs / DOCX here, or{" "}
            <span style={{ color: "#D91E7D" }} className="underline underline-offset-2 font-medium">
              browse
            </span>
          </p>
          <p className="text-xs text-gray-400">Multiple files supported</p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) => addFiles(e.target.files)}
          />
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <ul className="flex flex-col gap-2">
          {files.map((f) => (
            <li key={f.name}
              className="flex items-center justify-between gap-3 bg-white border
                           border-gray-200 rounded-lg px-4 py-2.5 shadow-sm">
              <div className="flex items-center gap-3 min-w-0">
                <span
                  className="text-xs font-bold uppercase px-1.5 py-0.5 rounded"
                  style={{
                    background: f.name.endsWith(".pdf") ? "#fde8f0" : "#ede8fd",
                    color: f.name.endsWith(".pdf") ? "#D91E7D" : "#7B2391",
                  }}
                >
                  {f.name.split(".").pop()}
                </span>
                <span className="text-sm text-gray-700 truncate">{f.name}</span>
                <span className="text-xs text-gray-400 shrink-0">{(f.size / 1024).toFixed(0)} KB</span>
              </div>
              <button
                onClick={() => removeFile(f.name)}
                className="text-gray-400 hover:text-red-500 transition-colors text-lg leading-none"
              >×</button>
            </li>
          ))}
        </ul>
      )}

      
        <div>
          <label className="block text-xs font-semibold text-gray-500 mb-2 tracking-wider uppercase">
            Matching Sensitivity
          </label>
          <div className="flex gap-2">
            {THRESHOLD_PRESETS.map((preset) => {
              const active = threshold === preset.value;
              return (
                <button
                  key={preset.value}
                  onClick={() => setThreshold(preset.value)}
                  className="flex-1 flex flex-col items-center gap-0.5 px-3 py-2.5 rounded-xl
                            border text-center transition-all"
                  style={{
                    borderColor: active ? "#7B2391" : "#e5e7eb",
                    background: active ? "#f9f5ff" : "#fafafa",
                    boxShadow: active ? "0 0 0 2px #7B239130" : "none",
                  }}
                >
                  <span
                    className="text-xs font-bold"
                    style={{ color: active ? "#7B2391" : "#374151" }}
                  >
                    {preset.label}
                  </span>
                  <span className="text-xs text-gray-400 leading-tight hidden sm:block">
                    {preset.description}
                  </span>
                  <span
                    className="text-xs font-mono mt-0.5"
                    style={{ color: active ? "#7B2391" : "#9ca3af" }}
                  >
                    ≥ {Math.round(preset.value * 100)}%
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      

      {/* Error */}
      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {/* Submit */}
      <button
        onClick={() => onScreen(files, threshold)}
        disabled={!canSubmit}
        className="w-full py-3 rounded-xl text-sm font-bold tracking-wide text-white transition-all duration-200"
        style={{
          background: canSubmit
            ? "linear-gradient(135deg, #1B3A8C, #7B2391, #D91E7D)"
            : "#e5e7eb",
          color: canSubmit ? "white" : "#9ca3af",
          cursor: canSubmit ? "pointer" : "not-allowed",
          boxShadow: canSubmit ? "0 4px 15px rgba(123,35,145,0.3)" : "none",
        }}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <Spinner /> Screening resumes…
          </span>
        ) : (
          `Screen ${files.length > 0 ? `${files.length} Resume${files.length > 1 ? "s" : ""}` : "Resumes"}`
        )}
      </button>
    </div>
  );
}

function UploadIcon({ dragging }) {
  return (
    <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"
      style={{ color: dragging ? "#D91E7D" : "#d1d5db" }}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  );
}