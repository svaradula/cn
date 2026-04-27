// src/components/ScheduleModal.jsx
// Phase 4 → Phase 5: Schedule Interview via Outlook deep-link
//
// How it works
// ------------
// No OAuth, no backend calls, no app registration needed.
// We construct an Outlook Web "compose event" URL with all fields
// pre-filled, then open it in a new tab. The HR user reviews and
// clicks "Send" inside Outlook — that's it.
//
// Outlook compose URL format:
//   https://outlook.office.com/calendar/action/compose
//     ?subject=<text>
//     &startdt=<ISO8601>
//     &enddt=<ISO8601>
//     &to=<email>
//     &body=<html or plain text>
//
// Supported by: Outlook Web, Outlook 365, outlook.live.com
// Works without any Azure app registration or admin consent.

import React, { useEffect, useState } from "react";

const BRAND = {
  navy:   "#1B3A8C",
  purple: "#7B2391",
  pink:   "#D91E7D",
  orange: "#F05A28",
};

// ── Email body template ────────────────────────────────────────────────────────

const buildEmailBody = (candidateName, roleName, hrName) =>
`Dear ${candidateName || "Candidate"},

Thank you for your interest in the ${roleName || "position"} role.

We are pleased to invite you for an interview. Please find the details in this calendar invitation.

What to expect:
- A technical discussion aligned to the role requirements
- An opportunity to ask questions about the team and role
- The session will last approximately 60 minutes

Please confirm your attendance by accepting this invitation. If you need to reschedule, kindly let us know at least 24 hours in advance.

We look forward to speaking with you.

Best regards,
${hrName || "The Recruitment Team"}`;

// ── Outlook deep-link builder ──────────────────────────────────────────────────

function buildOutlookUrl({ subject, startdt, enddt, toEmail, body }) {
  const base = "https://outlook.office.com/calendar/action/compose";
  const params = new URLSearchParams();
  if (subject)  params.set("subject", subject);
  if (startdt)  params.set("startdt", startdt);
  if (enddt)    params.set("enddt",   enddt);
  if (toEmail)  params.set("to",      toEmail);
  if (body)     params.set("body",    body);
  return `${base}?${params.toString()}`;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function ScheduleModal({
  candidate,
  roleName,
  hrEmail,
  onClose,
  onScheduled,
}) {
  const overlayRef = React.useRef(null);

  // Form fields
  const [hrName,     setHrName]     = useState("");
  const [ccEmails,   setCcEmails]   = useState("");
  const [subject,    setSubject]    = useState(`Interview for ${roleName || "the role"}`);
  const [body,       setBody]       = useState(
    buildEmailBody(candidate?.info?.name, roleName, "")
  );
  const [date,       setDate]       = useState("");
  const [time,       setTime]       = useState("10:00");
  const [duration,   setDuration]   = useState(60);
  const [timezone,   setTimezone]   = useState(
    Intl.DateTimeFormat().resolvedOptions().timeZone
  );

  // Set tomorrow as default date on mount
  useEffect(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    setDate(d.toISOString().split("T")[0]);
  }, []);

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Re-build body when hrName changes
  useEffect(() => {
    setBody(buildEmailBody(candidate?.info?.name, roleName, hrName));
  }, [hrName, roleName, candidate?.info?.name]);

  const canOpen =
    candidate?.info?.email &&
    candidate.info.email !== "Not found" &&
    date && time;

  const handleOpenOutlook = () => {
    if (!canOpen) return;

    // Build start/end datetime strings in LOCAL time.
    // IMPORTANT: do NOT use .toISOString() — it converts to UTC.
    // e.g. selecting 14:00 IST (UTC+5:30) → toISOString() gives 08:30Z
    // → Outlook shows 8:30 AM instead of 2:00 PM.
    // Passing the raw "YYYY-MM-DDTHH:MM:SS" string (no Z / timezone offset)
    // tells Outlook to treat it as the user's local time, matching the picker.
    const [hh, mm] = time.split(":").map(Number);
    const endTotalMins = hh * 60 + mm + duration;
    const endHH = String(Math.floor(endTotalMins / 60) % 24).padStart(2, "0");
    const endMM = String(endTotalMins % 60).padStart(2, "0");

    const startdt = `${date}T${time}:00`;            // e.g. "2025-09-15T14:00:00"
    const enddt   = `${date}T${endHH}:${endMM}:00`; // e.g. "2025-09-15T15:00:00"

    // CC note in body — Outlook deep-link doesn't have a CC param
    const ccNote = ccEmails.trim()
      ? `\n\nCC: ${ccEmails}\n`
      : "";

    const outlookUrl = buildOutlookUrl({
      subject,
      startdt,
      enddt,
      toEmail: candidate.info.email,
      body:    body + ccNote,
    });

    // Open Outlook in a new tab
    window.open(outlookUrl, "_blank", "noopener,noreferrer");

    // Move candidate to Phase 5 immediately — the HR user
    // completes the send inside Outlook
    onScheduled(candidate, {
      date,
      time,
      timezone,
      subject,
      teamsLink:    null,
      calendarLink: outlookUrl,
      scheduledAt:  new Date().toISOString(),
    });
  };

  return (
    <div
      ref={overlayRef}
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
      className="fixed inset-0 z-50 flex items-center justify-center px-4 py-6"
      style={{ background: "rgba(27,58,140,0.15)", backdropFilter: "blur(4px)" }}
    >
      <div
        className="relative w-full max-w-2xl h-[92vh] flex flex-col
                   rounded-2xl shadow-2xl overflow-hidden"
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
                  className="text-gray-400 hover:text-gray-700 transition-colors
                             text-2xl leading-none mt-0.5 shrink-0">
            ×
          </button>
        </div>

        {/* ── How it works banner ── */}
        <div className="mx-6 mt-4 shrink-0 rounded-xl px-4 py-3 flex items-start gap-3"
             style={{ background: "#f0f9ff", border: "1px solid #bae6fd" }}>
          <span className="text-lg shrink-0 mt-0.5">📅</span>
          <div>
            <p className="text-xs font-semibold text-blue-800">
              Opens directly in Outlook Calendar
            </p>
            <p className="text-xs text-blue-600 mt-0.5 leading-relaxed">
              Fill in the details below, then click <strong>Open in Outlook</strong>.
              Your Outlook event creation form will open in a new tab with everything
              pre-filled — just review and click <strong>Send</strong> inside Outlook.
            </p>
          </div>
        </div>

        {/* ── Scrollable form ── */}
        <div className="flex-1 min-h-0 overflow-y-auto px-6 py-5 flex flex-col gap-4">

          {/* Candidate summary */}
          <div className="rounded-xl p-3 flex items-center gap-3"
               style={{ background: "#f9f5ff", border: "1px solid #ede8fd" }}>
            <div className="w-9 h-9 rounded-full flex items-center justify-center
                            text-white font-bold text-xs shrink-0"
                 style={{ background: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple}, ${BRAND.pink})` }}>
              {getInitials(candidate?.info?.name)}
            </div>
            <div className="min-w-0 flex-1">
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

          {/* To — read-only */}
          <Field label="To (Candidate Email)">
            <input
              type="email"
              value={candidate?.info?.email || "No email found"}
              readOnly
              className="w-full px-3 py-2 text-sm rounded-lg border cursor-not-allowed text-gray-500"
              style={{ background: "#f9fafb", borderColor: "#e5e7eb" }}
            />
          </Field>

          {/* Your name */}
          <Field label="Your Name (appears in email sign-off)">
            <input
              type="text"
              value={hrName}
              onChange={(e) => setHrName(e.target.value)}
              placeholder="e.g. Sarah from Recruitment"
              className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                         focus:outline-none text-gray-800"
              onFocus={(e) => e.target.style.borderColor = BRAND.purple}
              onBlur={(e)  => e.target.style.borderColor = "#d1d5db"}
            />
          </Field>

          {/* CC note */}
          <Field label="CC (note — will be added to email body)">
            <input
              type="text"
              value={ccEmails}
              onChange={(e) => setCcEmails(e.target.value)}
              placeholder="manager@company.com, recruiter@company.com"
              className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                         focus:outline-none text-gray-800"
              onFocus={(e) => e.target.style.borderColor = BRAND.purple}
              onBlur={(e)  => e.target.style.borderColor = "#d1d5db"}
            />
            <p className="text-xs text-gray-400 mt-1">
              Add CC recipients manually inside Outlook after it opens.
            </p>
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
              onBlur={(e)  => e.target.style.borderColor = "#d1d5db"}
            />
          </Field>

          {/* Date + Time + Duration */}
          <div className="grid grid-cols-3 gap-3">
            <Field label="Date">
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                           focus:outline-none text-gray-800"
                onFocus={(e) => e.target.style.borderColor = BRAND.purple}
                onBlur={(e)  => e.target.style.borderColor = "#d1d5db"}
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
                onBlur={(e)  => e.target.style.borderColor = "#d1d5db"}
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

          {/* Timezone — informational */}
          <Field label="Your detected timezone">
            <input
              type="text"
              value={timezone}
              readOnly
              className="w-full px-3 py-2 text-sm rounded-lg border cursor-not-allowed text-gray-400"
              style={{ background: "#f9fafb", borderColor: "#e5e7eb" }}
            />
            <p className="text-xs text-gray-400 mt-1">
              Outlook will use your account's timezone setting automatically.
            </p>
          </Field>

          {/* Email body */}
          <Field label="Email Body (editable)">
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={10}
              className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300
                         focus:outline-none text-gray-700 resize-y leading-relaxed"
              onFocus={(e) => e.target.style.borderColor = BRAND.purple}
              onBlur={(e)  => e.target.style.borderColor = "#d1d5db"}
            />
          </Field>

          {/* Preview of Outlook URL */}
          {canOpen && (
            <div className="rounded-xl px-4 py-3"
                 style={{ background: "#f0fdf4", border: "1px solid #bbf7d0" }}>
              <p className="text-xs font-semibold text-green-700 mb-1">✓ Ready to open</p>
              <p className="text-xs text-green-600">
                Clicking the button will open Outlook in a new tab with the event
                pre-filled for <strong>{candidate?.info?.email}</strong> on{" "}
                <strong>{date} at {time}</strong> ({duration} min).
              </p>
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
            onClick={handleOpenOutlook}
            disabled={!canOpen}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm
                       font-bold text-white transition-all"
            style={{
              background: canOpen
                ? `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple}, ${BRAND.pink})`
                : "#e5e7eb",
              color:     canOpen ? "white" : "#9ca3af",
              cursor:    canOpen ? "pointer" : "not-allowed",
              boxShadow: canOpen ? "0 4px 12px rgba(123,35,145,0.25)" : "none",
            }}
          >
            <OutlookIcon />
            Open in Outlook Calendar
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

function getInitials(name) {
  if (!name || name === "Not found") return "?";
  return name.trim().split(/\s+/).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
}

function OutlookIcon() {
  return (
    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="3" fill="#0078D4"/>
      <path d="M13 5h7v14h-7V5z" fill="#28A8E8"/>
      <path d="M4 7h9v10H4V7z" fill="white" opacity="0.9"/>
      <text x="6.5" y="15" fontSize="7" fontWeight="bold" fill="#0078D4">O</text>
    </svg>
  );
}