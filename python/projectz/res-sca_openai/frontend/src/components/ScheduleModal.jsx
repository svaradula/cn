// src/components/ScheduleModal.jsx
// Phase 4 → Phase 5: Schedule Interview modal
// Integrates with Microsoft Graph API (Outlook + Teams)

import React, { useEffect, useRef, useState } from "react";

const BRAND = {
  navy:   "#1B3A8C",
  purple: "#7B2391",
  pink:   "#D91E7D",
  orange: "#F05A28",
};

// Default email body template
const buildEmailBody = (candidateName, roleName, interviewerName) => `<p>Dear ${candidateName || "Candidate"},</p>

<p>Thank you for your interest in the <strong>${roleName || "position"}</strong> role at our organisation. We are pleased to invite you for an interview.</p>

<p>Please find the details of your interview below. A Microsoft Teams meeting link will be included in this invitation for your convenience.</p>

<p><strong>What to expect:</strong></p>
<ul>
  <li>A technical discussion aligned to the role requirements</li>
  <li>An opportunity for you to ask questions about the team and the role</li>
  <li>The session will last approximately 60 minutes</li>
</ul>

<p>Please confirm your attendance by replying to this email. If you need to reschedule, kindly let us know at least 24 hours in advance.</p>

<p>We look forward to speaking with you.</p>

<p>Best regards,<br/>${interviewerName || "The Recruitment Team"}</p>`;

export default function ScheduleModal({
  candidate,      // { filename, info: {name, email, phone}, score }
  roleName,       // extracted from JD
  hrEmail,        // logged-in HR user's email
  isAuthenticated,
  onClose,
  onScheduled,    // (candidate, scheduleDetails) → move to Phase 5
}) {
  const overlayRef = useRef(null);

  // Form state
  const [fromEmail,  setFromEmail]  = useState(hrEmail || "");
  const [ccEmails,   setCcEmails]   = useState("");
  const [subject,    setSubject]    = useState(`Interview for ${roleName || "the role"}`);
  const [body,       setBody]       = useState(
    buildEmailBody(candidate?.info?.name, roleName, "")
  );
  const [date,       setDate]       = useState("");
  const [time,       setTime]       = useState("10:00");
  const [timezone,   setTimezone]   = useState(
    Intl.DateTimeFormat().resolvedOptions().timeZone
  );
  const [duration,   setDuration]   = useState(60);
  const [includeTeams, setIncludeTeams] = useState(true);

  // UI state
  const [submitting, setSubmitting] = useState(false);
  const [error,      setError]      = useState(null);

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Auto-set tomorrow as default date
  useEffect(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setDate(tomorrow.toISOString().split("T")[0]);
  }, []);

  const canSubmit =
    isAuthenticated &&
    fromEmail.trim() &&
    candidate?.info?.email &&
    candidate.info.email !== "Not found" &&
    date &&
    time &&
    !submitting;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);

    const interviewDt = new Date(`${date}T${time}:00`).toISOString();
    const ccList = ccEmails
      .split(/[,;\n]/)
      .map((e) => e.trim())
      .filter(Boolean);

    try {
      const res = await fetch(
        `${import.meta.env.VITE_API_BASE_URL}/api/schedule-interview`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            from_email:     fromEmail,
            to_email:       candidate.info.email,
            cc_emails:      ccList,
            subject,
            body,
            interview_dt:   interviewDt,
            timezone,
            duration_min:   duration,
            include_teams:  includeTeams,
            candidate_name: candidate.info.name,
            role_name:      roleName,
          }),
        }
      );

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? "Scheduling failed");
      }

      const data = await res.json();

      // Pass schedule details up to App for Phase 5
      onScheduled(candidate, {
        date,
        time,
        timezone,
        subject,
        teamsLink: data.teams_link,
        calendarLink: data.calendar_link,
        scheduledAt: new Date().toISOString(),
      });

    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  };

  const handleConnectOutlook = () => {
    window.location.href = `${import.meta.env.VITE_API_BASE_URL}/api/auth/login`;
  };

  return (
    <div
      ref={overlayRef}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
      className="fixed inset-0 z-50 flex items-center justify-center px-4 py-6"
      style={{ background: "rgba(27,58,140,0.15)", backdropFilter: "blur(4px)" }}
    >
      <div
        className="relative w-full max-w-2xl h-[92vh] flex flex-col rounded-2xl
                   shadow-2xl overflow-hidden"
        style={{ background: "white", border: "1px solid #e5e7eb" }}
      >
        {/* Gradient top bar */}
        <div className="h-1 w-full shrink-0"
             style={{ background: `linear-gradient(90deg, ${BRAND.navy}, ${BRAND.purple}, ${BRAND.pink}, ${BRAND.orange})` }} />

        {/* ── Header ── */}
        <div className="flex items-start justify-between gap-4 px-6 py-4
                        border-b border-gray-100 shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold tracking-widest text-white px-2 py-0.5 rounded"
                    style={{ background: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple})` }}>
                PHASE 05
              </span>
              <span className="text-xs text-gray-400">· Schedule Interview</span>
            </div>
            <h2 className="text-base font-bold text-gray-900">Schedule Interview</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {candidate?.info?.name || candidate?.filename}
            </p>
          </div>
          <button onClick={onClose}
                  className="text-gray-400 hover:text-gray-700 transition-colors text-2xl leading-none mt-0.5">
            ×
          </button>
        </div>

        {/* ── Auth banner (shown if not connected) ── */}
        {!isAuthenticated && (
          <div className="mx-6 mt-4 shrink-0 flex flex-col gap-2">
            {/* Primary connect button */}
            <div className="rounded-xl px-4 py-3 flex items-center justify-between gap-4"
                 style={{ background: "#fffbeb", border: "1px solid #fde68a" }}>
              <div className="flex items-center gap-3">
                <span className="text-lg">🔗</span>
                <div>
                  <p className="text-xs font-semibold text-amber-800">Connect your Outlook account</p>
                  <p className="text-xs text-amber-600">Required to send emails and create Teams meetings</p>
                </div>
              </div>
              <button
                onClick={handleConnectOutlook}
                className="text-xs font-bold text-white px-3 py-1.5 rounded-lg shrink-0 transition-opacity hover:opacity-90"
                style={{ background: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple})` }}
              >
                Connect Outlook
              </button>
            </div>

            {/* Admin consent helper — shown when org policy blocks user consent */}
            <div className="rounded-xl px-4 py-3"
                 style={{ background: "#f0f9ff", border: "1px solid #bae6fd" }}>
              <p className="text-xs font-semibold text-blue-800 mb-1">
                Seeing 'Approval required' or 'Request pending'?
              </p>
              <p className="text-xs text-blue-600 mb-2">
                Your organisation requires a Global Admin to approve this app once.
                Copy the link below and send it to your IT/Azure admin.
              </p>
              <AdminConsentUrl apiBase={import.meta.env.VITE_API_BASE_URL} />
            </div>
          </div>
        )}

        {/* ── Scrollable form body ── */}
        <div className="flex-1 min-h-0 overflow-y-auto px-6 py-5 flex flex-col gap-4">

          {/* Candidate summary */}
          <div className="rounded-xl p-3 flex items-center gap-3"
               style={{ background: "#f9f5ff", border: "1px solid #ede8fd" }}>
            <div className="w-9 h-9 rounded-full flex items-center justify-center text-white
                            font-bold text-xs shrink-0"
                 style={{ background: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple}, ${BRAND.pink})` }}>
              {getInitials(candidate?.info?.name)}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-gray-800 truncate">
                {candidate?.info?.name || "Unknown"}
              </p>
              <p className="text-xs text-gray-500">{candidate?.info?.email}</p>
            </div>
            {candidate?.score && (
              <span className="ml-auto text-xs font-bold px-2 py-0.5 rounded-full shrink-0"
                    style={{ background: "#ede8fd", color: BRAND.purple, border: "1px solid #c4b0f0" }}>
                {Math.round(candidate.score * 100)}% match
              </span>
            )}
          </div>

          {/* From */}
          <Field label="From (HR Email)">
            <input
              type="email"
              value={fromEmail}
              onChange={(e) => setFromEmail(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                         focus:outline-none text-gray-800"
              onFocus={(e) => e.target.style.borderColor = BRAND.purple}
              onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
              placeholder="your@company.com"
            />
          </Field>

          {/* To — read-only */}
          <Field label="To (Candidate Email)">
            <input
              type="email"
              value={candidate?.info?.email || ""}
              readOnly
              className="w-full px-3 py-2 text-sm rounded-lg border text-gray-500 cursor-not-allowed"
              style={{ background: "#f9fafb", borderColor: "#e5e7eb" }}
            />
          </Field>

          {/* CC */}
          <Field label="CC (optional, comma-separated)">
            <input
              type="text"
              value={ccEmails}
              onChange={(e) => setCcEmails(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                         focus:outline-none text-gray-800"
              onFocus={(e) => e.target.style.borderColor = BRAND.purple}
              onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
              placeholder="manager@company.com, recruiter@company.com"
            />
          </Field>

          {/* Subject */}
          <Field label="Subject">
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                         focus:outline-none text-gray-800"
              onFocus={(e) => e.target.style.borderColor = BRAND.purple}
              onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
            />
          </Field>

          {/* Date + Time + Duration in a row */}
          <div className="grid grid-cols-3 gap-3">
            <Field label="Date">
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                           focus:outline-none text-gray-800"
                onFocus={(e) => e.target.style.borderColor = BRAND.purple}
                onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
              />
            </Field>
            <Field label="Time">
              <input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                           focus:outline-none text-gray-800"
                onFocus={(e) => e.target.style.borderColor = BRAND.purple}
                onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
              />
            </Field>
            <Field label="Duration">
              <select
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                           focus:outline-none text-gray-800 bg-white"
              >
                <option value={30}>30 min</option>
                <option value={45}>45 min</option>
                <option value={60}>60 min</option>
                <option value={90}>90 min</option>
                <option value={120}>2 hours</option>
              </select>
            </Field>
          </div>

          {/* Timezone */}
          <Field label="Timezone">
            <input
              type="text"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                         focus:outline-none text-gray-800"
              onFocus={(e) => e.target.style.borderColor = BRAND.purple}
              onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
            />
          </Field>

          {/* Teams toggle */}
          <div className="flex items-center justify-between px-4 py-3 rounded-xl"
               style={{ background: "#f9f5ff", border: "1px solid #ede8fd" }}>
            <div className="flex items-center gap-3">
              <TeamsIcon />
              <div>
                <p className="text-xs font-semibold text-gray-700">Include Teams Meeting Link</p>
                <p className="text-xs text-gray-400">Automatically generate a Teams invite</p>
              </div>
            </div>
            <Toggle checked={includeTeams} onChange={setIncludeTeams} />
          </div>

          {/* Email body */}
          <Field label="Email Body (HTML)">
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={10}
              className="w-full px-3 py-2 text-xs rounded-lg border border-gray-300
                         focus:outline-none text-gray-700 resize-y font-mono leading-relaxed"
              onFocus={(e) => e.target.style.borderColor = BRAND.purple}
              onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
            />
            <p className="text-xs text-gray-400 mt-1">
              Supports HTML. The Teams meeting link will be appended automatically.
            </p>
          </Field>

          {/* Error */}
          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200
                            rounded-lg px-4 py-3">
              {error}
            </div>
          )}
        </div>

        {/* ── Footer ── */}
        <div className="border-t border-gray-100 px-6 py-4 shrink-0 bg-gray-50
                        flex items-center justify-between gap-4">
          <button
            onClick={onClose}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            Cancel
          </button>

          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold
                       text-white transition-all"
            style={{
              background: canSubmit
                ? `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple}, ${BRAND.pink})`
                : "#e5e7eb",
              color:     canSubmit ? "white" : "#9ca3af",
              cursor:    canSubmit ? "pointer" : "not-allowed",
              boxShadow: canSubmit ? "0 4px 12px rgba(123,35,145,0.25)" : "none",
            }}
          >
            {submitting ? (
              <><Spinner /> Scheduling…</>
            ) : (
              <><SendIcon /> Send & Schedule Interview</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Small components ──────────────────────────────────────────────────────────

function Field({ label, children }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-gray-500 tracking-wider uppercase">
        {label}
      </label>
      {children}
    </div>
  );
}

function Toggle({ checked, onChange }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className="relative w-11 h-6 rounded-full transition-colors duration-200 shrink-0"
      style={{ background: checked ? BRAND.purple : "#d1d5db" }}
    >
      <span
        className="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200"
        style={{ transform: checked ? "translateX(22px)" : "translateX(2px)" }}
      />
    </button>
  );
}

function getInitials(name) {
  if (!name || name === "Not found") return "?";
  return name.trim().split(/\s+/).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
}

function AdminConsentUrl({ apiBase }) {
  const [url, setUrl] = React.useState("");
  const [copied, setCopied] = React.useState(false);

  React.useEffect(() => {
    fetch(`${apiBase}/api/auth/admin-consent-url`)
      .then((r) => r.json())
      .then((d) => setUrl(d.admin_consent_url || ""))
      .catch(() => {});
  }, [apiBase]);

  const copy = () => {
    if (!url) return;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  if (!url) return null;

  return (
    <div className="flex items-center gap-2">
      <input
        readOnly
        value={url}
        className="flex-1 text-xs px-2 py-1.5 rounded border border-blue-200
                   bg-white text-blue-700 truncate font-mono"
      />
      <button
        onClick={copy}
        className="text-xs font-bold px-2.5 py-1.5 rounded-lg shrink-0
                   transition-colors"
        style={{ background: copied ? "#16a34a" : "#1d4ed8", color: "white" }}
      >
        {copied ? "Copied ✓" : "Copy"}
      </button>
    </div>
  );
}

function TeamsIcon() {
  return (
    <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="4" fill="#5059C9"/>
      <path d="M14 7h3a2 2 0 012 2v4a2 2 0 01-2 2h-3V7z" fill="#7B83EB"/>
      <circle cx="15.5" cy="5.5" r="1.5" fill="#7B83EB"/>
      <rect x="5" y="9" width="10" height="8" rx="2" fill="white"/>
      <path d="M8 13h4M10 11v4" stroke="#5059C9" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

function SendIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
    </svg>
  );
}