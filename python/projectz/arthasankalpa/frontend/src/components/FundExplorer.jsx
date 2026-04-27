/**
 * FundExplorer.jsx - Search, filter, and compare mutual funds.
 */
import { useState } from "react";
import { Search, Star, X } from "lucide-react";
import { useFundSearch } from "../hooks/useFunds";

const CATEGORIES = [
  { value: "",       label: "All"    },
  { value: "equity", label: "Equity" },
  { value: "debt",   label: "Debt"   },
  { value: "hybrid", label: "Hybrid" },
  { value: "index",  label: "Index"  },
];

const RISKS = [
  { value: "",       label: "Any Risk"  },
  { value: "low",    label: "Low"       },
  { value: "medium", label: "Moderate"  },
  { value: "high",   label: "High"      },
];

function Stars({ count }) {
  return (
    <div className="flex gap-0.5">
      {[1,2,3,4,5].map((n) => (
        <Star key={n} size={10}
          className={n <= (count || 0) ? "text-amber-400 fill-amber-400" : "text-gray-200"} />
      ))}
    </div>
  );
}

function RiskBadge({ risk }) {
  const styles = {
    low:      "bg-emerald-50 text-emerald-700 border-emerald-100",
    moderate: "bg-amber-50 text-amber-700 border-amber-100",
    high:     "bg-red-50 text-red-700 border-red-100",
  };
  return (
    <span className={"text-xs px-2 py-0.5 rounded-full border font-medium " +
      (styles[risk] || styles.moderate)}>
      {risk ? risk.charAt(0).toUpperCase() + risk.slice(1) : "Moderate"}
    </span>
  );
}

function ReturnVal({ value, label }) {
  if (value == null) return <div className="text-center"><div className="text-xs text-gray-300">N/A</div><div className="text-xs text-gray-400">{label}</div></div>;
  const pos = value >= 0;
  return (
    <div className="text-center">
      <div className={"text-sm font-semibold " + (pos ? "text-emerald-600" : "text-red-500")}>
        {pos ? "+" : ""}{value.toFixed(1)}%
      </div>
      <div className="text-xs text-gray-400">{label}</div>
    </div>
  );
}

function FundCard({ fund, selected, onAdd, onRemove }) {
  return (
    <div className={"bg-white rounded-xl border p-4 transition-all hover:shadow-md " +
      (selected ? "border-blue-400 ring-1 ring-blue-300" : "border-gray-100")}>
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900 text-sm leading-tight line-clamp-2">{fund.scheme_name}</p>
          <p className="text-xs text-gray-400 mt-0.5">{fund.category}</p>
        </div>
        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <RiskBadge risk={fund.risk_rating} />
          {fund.rating_stars && <Stars count={fund.rating_stars} />}
        </div>
      </div>

      <div className="flex items-baseline gap-1 mb-3">
        <span className="text-lg font-bold text-gray-900">Rs.{Number(fund.nav || 0).toFixed(4)}</span>
        <span className="text-xs text-gray-400">NAV</span>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3 bg-gray-50 rounded-lg p-2">
        <ReturnVal value={fund.returns_1y} label="1Y" />
        <ReturnVal value={fund.returns_3y} label="3Y CAGR" />
        <ReturnVal value={fund.returns_5y} label="5Y CAGR" />
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
        <span>Sharpe: <strong className="text-gray-700">{fund.sharpe_ratio != null ? Number(fund.sharpe_ratio).toFixed(2) : "N/A"}</strong></span>
        <span>Exp: <strong className="text-gray-700">{fund.expense_ratio != null ? Number(fund.expense_ratio).toFixed(2) + "%" : "N/A"}</strong></span>
      </div>

      {selected ? (
        <button onClick={() => onRemove(fund)}
          className="w-full text-xs py-1.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-200 hover:bg-blue-100 flex items-center justify-center gap-1">
          <X size={11} /> Remove
        </button>
      ) : (
        <button onClick={() => onAdd(fund)}
          className="w-full text-xs py-1.5 rounded-lg bg-gray-50 text-gray-600 border border-gray-200 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 transition-colors">
          + Compare
        </button>
      )}
    </div>
  );
}

function CompareTable({ funds, onRemove }) {
  const rows = [
    { key: "nav",          label: "NAV (Rs.)",     fmt: (v) => "Rs." + Number(v || 0).toFixed(4) },
    { key: "returns_1y",   label: "1Y Return",     fmt: (v) => v != null ? (v >= 0 ? "+" : "") + Number(v).toFixed(1) + "%" : "N/A", hl: true },
    { key: "returns_3y",   label: "3Y CAGR",       fmt: (v) => v != null ? (v >= 0 ? "+" : "") + Number(v).toFixed(1) + "%" : "N/A", hl: true },
    { key: "returns_5y",   label: "5Y CAGR",       fmt: (v) => v != null ? (v >= 0 ? "+" : "") + Number(v).toFixed(1) + "%" : "N/A", hl: true },
    { key: "sharpe_ratio", label: "Sharpe Ratio",  fmt: (v) => v != null ? Number(v).toFixed(2) : "N/A", hl: true },
    { key: "expense_ratio",label: "Expense Ratio", fmt: (v) => v != null ? Number(v).toFixed(2) + "%" : "N/A", rev: true },
    { key: "risk_rating",  label: "Risk",          fmt: (v) => (v || "").toUpperCase() },
  ];

  const best = (key, rev) => {
    const vals = funds.map((f) => f[key]).filter((v) => v != null);
    if (!vals.length) return null;
    return rev ? Math.min(...vals) : Math.max(...vals);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-auto shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-100">
            <th className="text-left p-3 text-xs font-medium text-gray-500 w-32">Metric</th>
            {funds.map((f) => (
              <th key={f.scheme_code} className="p-3 text-left">
                <div className="font-semibold text-gray-800 text-xs leading-tight max-w-48">{f.scheme_name}</div>
                <div className="text-xs text-gray-400 font-normal mt-0.5">{f.category}</div>
                <button onClick={() => onRemove(f)} className="text-xs text-red-400 hover:text-red-600 mt-1 flex items-center gap-0.5">
                  <X size={10} /> Remove
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const b = r.hl ? best(r.key, r.rev) : null;
            return (
              <tr key={r.key} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="p-3 text-xs text-gray-500 font-medium">{r.label}</td>
                {funds.map((f) => {
                  const val = f[r.key];
                  const isBest = b != null && val === b;
                  return (
                    <td key={f.scheme_code} className={"p-3 font-medium text-sm " + (isBest ? "text-emerald-600" : "text-gray-700")}>
                      {isBest && <span className="mr-1 text-xs">*</span>}
                      {r.fmt(val)}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function FundExplorer() {
  const [query, setQuery]         = useState("");
  const [category, setCategory]   = useState("");
  const [risk, setRisk]           = useState("");
  const [compared, setCompared]   = useState([]);
  const [showCmp, setShowCmp]     = useState(false);
  const { results, loading, error, search } = useFundSearch();

  const doSearch = () => {
    search({ q: query || "mutual fund India", category: category || undefined, risk: risk || undefined, limit: 20 });
  };

  const add = (f) => {
    if (compared.length >= 3) { alert("Max 3 funds"); return; }
    if (!compared.find((c) => c.scheme_code === f.scheme_code))
      setCompared((p) => [...p, f]);
  };
  const remove = (f) => setCompared((p) => p.filter((c) => c.scheme_code !== f.scheme_code));

  const pillBase = "px-3 py-1 text-xs rounded-full border transition-all cursor-pointer";
  const pillOff  = pillBase + " text-gray-600 border-gray-200 hover:border-blue-300";
  const pillOn   = pillBase + " bg-blue-600 text-white border-blue-600";

  return (
    <div className="flex flex-col gap-5">

      {/* Search */}
      <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
        <h2 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
          <Search size={16} className="text-blue-500" /> Fund Explorer
        </h2>
        <div className="flex gap-2 mb-3">
          <input value={query} onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && doSearch()}
            placeholder="Search: ELSS, large cap, Mirae, HDFC..."
            className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <button onClick={doSearch} disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors">
            {loading ? "..." : "Search"}
          </button>
        </div>
        <div className="flex gap-2 flex-wrap">
          {CATEGORIES.map((c) => (
            <button key={c.value} onClick={() => setCategory(c.value)}
              className={category === c.value ? pillOn : pillOff}>{c.label}</button>
          ))}
          <span className="text-gray-300 text-xs self-center">|</span>
          {RISKS.map((r) => (
            <button key={r.value} onClick={() => setRisk(r.value)}
              className={risk === r.value ? pillOn.replace("bg-blue-600 border-blue-600", "bg-emerald-600 border-emerald-600") : pillOff}>{r.label}</button>
          ))}
        </div>
      </div>

      {/* Compare bar */}
      {compared.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 flex items-center justify-between">
          <span className="text-sm text-blue-700 font-medium">{compared.length} fund{compared.length > 1 ? "s" : ""} selected</span>
          <div className="flex gap-2">
            {compared.length >= 2 && (
              <button onClick={() => setShowCmp(!showCmp)}
                className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700">
                {showCmp ? "Hide" : "Compare Now"}
              </button>
            )}
            <button onClick={() => { setCompared([]); setShowCmp(false); }} className="text-xs text-blue-500 hover:text-blue-700">Clear</button>
          </div>
        </div>
      )}

      {/* Compare table */}
      {showCmp && compared.length >= 2 && <CompareTable funds={compared} onRemove={remove} />}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-600">{error}</div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 mb-3">{results.length} funds found</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((f) => (
              <FundCard key={f.scheme_code} fund={f}
                selected={!!compared.find((c) => c.scheme_code === f.scheme_code)}
                onAdd={add} onRemove={remove} />
            ))}
          </div>
        </div>
      )}

      {results.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-400">
          <Search size={32} className="mx-auto mb-3 opacity-30" />
          <p>Search for mutual funds above to get started</p>
        </div>
      )}
    </div>
  );
}