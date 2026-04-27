// src/components/ScheduledCandidates.jsx
// Phase 5 — Candidates with confirmed interview schedules

const BRAND = {
  navy:   "#1B3A8C",
  purple: "#7B2391",
  pink:   "#D91E7D",
  orange: "#F05A28",
};

export default function ScheduledCandidates({ candidates }) {
  if (candidates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48
                      border-2 border-dashed rounded-xl"
           style={{ borderColor: "#e5e7eb" }}>
        <CalendarCheckIcon />
        <p className="mt-3 text-sm text-gray-300">No interviews scheduled yet</p>
        <p className="text-xs mt-1 text-gray-300">
          Schedule interviews from Phase 4 to see them here
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {candidates.map((entry, idx) => (
        <ScheduledRow key={entry.candidate.filename} rank={idx + 1} entry={entry} />
      ))}

      <div className="mt-1 px-4 py-3 rounded-xl flex items-center justify-between"
           style={{ background: "#f0fdf4", border: "1px solid #bbf7d0" }}>
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded-full flex items-center justify-center
                           text-white text-xs font-bold"
                style={{ background: "linear-gradient(135deg, #16a34a, #15803d)" }}>
            {candidates.length}
          </span>
          <span className="text-xs font-semibold text-green-700">
            interview{candidates.length > 1 ? "s" : ""} scheduled
          </span>
        </div>
        <span className="text-xs text-green-500">Phase 5</span>
      </div>
    </div>
  );
}

function ScheduledRow({ rank, entry }) {
  const { candidate, schedule } = entry;
  const { name, email } = candidate.info;
  const notFound = (v) => !v || v === "Not found";

  const formattedDate = schedule.date
    ? new Date(`${schedule.date}T${schedule.time}`).toLocaleDateString("en-GB", {
        weekday: "short", day: "numeric", month: "short", year: "numeric",
      })
    : "";

  const formattedTime = schedule.time
    ? new Date(`${schedule.date}T${schedule.time}`).toLocaleTimeString("en-GB", {
        hour: "2-digit", minute: "2-digit",
      })
    : "";

  return (
    <div className="bg-white rounded-xl border p-4 shadow-sm hover:shadow-md transition-all"
         style={{ borderColor: "#e5e7eb" }}>
      <div className="flex items-start gap-4">

        {/* Avatar */}
        <div className="relative shrink-0">
          <div className="w-11 h-11 rounded-full flex items-center justify-center
                          text-white font-bold text-sm select-none"
               style={{ background: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple}, ${BRAND.pink})` }}>
            {getInitials(name)}
          </div>
          <div className="absolute -top-1 -left-1 w-4 h-4 rounded-full flex items-center
                          justify-center text-white text-xs font-bold"
               style={{ background: "#16a34a", fontSize: "9px" }}>
            {rank}
          </div>
        </div>

        {/* Info block */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">
            {notFound(name) ? <span className="text-gray-400 italic text-xs">Name not found</span> : name}
          </p>
          <p className="text-xs text-gray-400 truncate mt-0.5">{email}</p>

          {/* Interview details */}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <span className="flex items-center gap-1 text-xs text-gray-600">
              <CalendarIcon />
              {formattedDate} at {formattedTime}
            </span>
            {schedule.timezone && (
              <span className="text-xs text-gray-400">({schedule.timezone})</span>
            )}
          </div>

          {/* Subject */}
          {schedule.subject && (
            <p className="text-xs text-gray-500 mt-1 truncate">
              📧 {schedule.subject}
            </p>
          )}
        </div>

        {/* Right badges */}
        <div className="shrink-0 flex flex-col items-end gap-2">
          {/* Confirmed badge */}
          <span className="flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-lg"
                style={{ background: "#f0fdf4", color: "#16a34a", border: "1px solid #bbf7d0" }}>
            <CheckIcon /> Confirmed
          </span>

          {/* Teams link */}
          {schedule.teamsLink && (
            <a href={schedule.teamsLink} target="_blank" rel="noopener noreferrer"
               className="flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-lg
                          transition-opacity hover:opacity-80"
               style={{ background: "#eef2ff", color: "#4f46e5", border: "1px solid #c7d2fe" }}>
              <TeamsIcon /> Join Teams
            </a>
          )}

          {/* Calendar link */}
          {schedule.calendarLink && (
            <a href={schedule.calendarLink} target="_blank" rel="noopener noreferrer"
               className="flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-lg
                          transition-opacity hover:opacity-80"
               style={{ background: "#eff6ff", color: BRAND.navy, border: "1px solid #bfdbfe" }}>
              <CalendarIcon /> View Event
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function getInitials(name) {
  if (!name || name === "Not found") return "?";
  return name.trim().split(/\s+/).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
}

function CheckIcon() {
  return (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  );
}
function CalendarCheckIcon() {
  return (
    <svg className="w-10 h-10 text-gray-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2
           M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
    </svg>
  );
}
function CalendarIcon() {
  return (
    <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );
}
function TeamsIcon() {
  return (
    <svg className="w-3 h-3" viewBox="0 0 24 24" fill="#5059C9">
      <rect width="24" height="24" rx="3" fill="#5059C9"/>
      <rect x="6" y="10" width="8" height="6" rx="1.5" fill="white"/>
      <circle cx="14.5" cy="7.5" r="1.5" fill="#7B83EB"/>
      <rect x="12" y="9" width="5" height="4" rx="1" fill="#7B83EB"/>
    </svg>
  );
}