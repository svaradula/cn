// src/components/SelectedCandidates.jsx
// Phase 4 — Selected candidates with Schedule Interview button

const BRAND = {
  navy:   "#1B3A8C",
  purple: "#7B2391",
  pink:   "#D91E7D",
  orange: "#F05A28",
};

export default function SelectedCandidates({ candidates, onRemove, onSchedule }) {
  if (candidates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48
                      border-2 border-dashed rounded-xl text-gray-400"
           style={{ borderColor: "#e5e7eb" }}>
        <CalendarIcon />
        <p className="mt-3 text-sm text-gray-400">No candidates selected yet</p>
        <p className="text-xs mt-1 text-gray-300">
          Shortlist candidates from the interview questions popup
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {candidates.map((c, idx) => (
        <CandidateRow
          key={c.filename}
          rank={idx + 1}
          candidate={c}
          onRemove={() => onRemove(c.filename)}
          onSchedule={() => onSchedule(c)}
        />
      ))}

      <div className="mt-1 px-4 py-3 rounded-xl flex items-center justify-between"
           style={{ background: "#f9f5ff", border: "1px solid #ede8fd" }}>
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded-full flex items-center justify-center
                           text-white text-xs font-bold"
                style={{ background: `linear-gradient(135deg, ${BRAND.purple}, ${BRAND.pink})` }}>
            {candidates.length}
          </span>
          <span className="text-xs font-semibold text-gray-600">
            candidate{candidates.length > 1 ? "s" : ""} ready for scheduling
          </span>
        </div>
        <span className="text-xs text-gray-400">Phase 4</span>
      </div>
    </div>
  );
}

function CandidateRow({ rank, candidate, onRemove, onSchedule }) {
  const { name, email, phone } = candidate.info;
  const notFound = (v) => !v || v === "Not found";

  return (
    <div className="bg-white rounded-xl border p-4 shadow-sm hover:shadow-md transition-all"
         style={{ borderColor: "#e5e7eb" }}>
      <div className="flex items-center gap-4">

        {/* Avatar */}
        <div className="relative shrink-0">
          <div className="w-11 h-11 rounded-full flex items-center justify-center
                          text-white font-bold text-sm select-none"
               style={{ background: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple}, ${BRAND.pink})` }}>
            {getInitials(name)}
          </div>
          <div className="absolute -top-1 -left-1 w-4 h-4 rounded-full flex items-center
                          justify-center text-white font-bold"
               style={{ background: BRAND.purple, fontSize: "9px" }}>
            {rank}
          </div>
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">
            {notFound(name)
              ? <span className="text-gray-400 font-normal italic text-xs">Name not found</span>
              : name}
          </p>
          <p className="text-xs text-gray-400 truncate mt-0.5">{candidate.filename}</p>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5">
            {!notFound(email) && (
              <a href={`mailto:${email}`}
                 className="flex items-center gap-1 text-xs transition-opacity hover:opacity-70"
                 style={{ color: BRAND.purple }}>
                <EmailIcon /> {email}
              </a>
            )}
            {!notFound(phone) && (
              <a href={`tel:${phone}`}
                 className="flex items-center gap-1 text-xs transition-opacity hover:opacity-70"
                 style={{ color: BRAND.navy }}>
                <PhoneIcon /> {phone}
              </a>
            )}
          </div>
        </div>

        {/* Score */}
        {candidate.score != null && (
          <div className="shrink-0 flex flex-col items-center gap-0.5">
            <span className="text-xs font-bold px-2 py-0.5 rounded-full"
                  style={{ background: "#ede8fd", color: BRAND.purple, border: "1px solid #c4b0f0" }}>
              {Math.round(candidate.score * 100)}%
            </span>
            <span className="text-xs text-gray-400">match</span>
          </div>
        )}

        {/* Actions */}
        <div className="shrink-0 flex flex-col items-end gap-2">
          {/* Primary: Schedule Interview */}
          <button
            onClick={onSchedule}
            className="flex items-center gap-1.5 text-xs font-bold px-3 py-2 rounded-lg
                       text-white transition-all hover:opacity-90"
            style={{
              background: `linear-gradient(135deg, ${BRAND.navy}, ${BRAND.purple})`,
              boxShadow: "0 2px 8px rgba(27,58,140,0.25)",
            }}
          >
            <CalendarIcon white /> Schedule Interview
          </button>

          {/* Secondary: Remove */}
          <button
            onClick={onRemove}
            className="text-xs text-gray-400 hover:text-red-500 transition-colors
                       flex items-center gap-1"
          >
            <RemoveIcon /> Remove
          </button>
        </div>
      </div>
    </div>
  );
}

function getInitials(name) {
  if (!name || name === "Not found") return "?";
  return name.trim().split(/\s+/).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
}

function CalendarIcon({ white } = {}) {
  return (
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"
         style={{ color: white ? "white" : "#9ca3af" }}>
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );
}
function RemoveIcon() {
  return (
    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  );
}
function EmailIcon() {
  return (
    <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}
function PhoneIcon() {
  return (
    <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13
           a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2
           2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
    </svg>
  );
}