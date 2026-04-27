/**
 * RiskProfiler.jsx - Multi-step risk profiling form.
 */
import { useState } from "react";
import { ChevronRight, ChevronLeft, ShieldCheck } from "lucide-react";
import { profileApi } from "../services/api";

const STEPS = [
  { id: "basics",  title: "About You",     emoji: "Person" },
  { id: "finance", title: "Your Finances",  emoji: "Money"  },
  { id: "goals",   title: "Goals & Risk",   emoji: "Target" },
];

const GOALS = ["Retirement", "Child Education", "Home Purchase", "Emergency Fund", "Wealth Creation", "Tax Saving"];

const inp  = "w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white";
const lbl  = "block text-sm font-medium text-gray-700 mb-1.5";

function Step({ current, total }) {
  return (
    <div className="flex items-center justify-center gap-2 mb-6">
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} className={"h-1.5 rounded-full transition-all " +
          (i < current ? "bg-blue-600 w-8" : i === current ? "bg-blue-400 w-8" : "bg-gray-200 w-4")} />
      ))}
    </div>
  );
}

export default function RiskProfiler({ onProfileSaved }) {
  const [step, setStep]       = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState(null);

  const [form, setForm] = useState({
    user_id:                  "user_" + Date.now(),
    age:                      "",
    monthly_income_inr:       "",
    monthly_expenses_inr:     "",
    existing_investments_inr: "0",
    risk_appetite:            "medium",
    investment_horizon:       "long",
    financial_goals:          [],
    tax_bracket_pct:          "30",
  });

  const set = (k) => (e) => setForm((p) => ({ ...p, [k]: e.target.value }));

  const toggleGoal = (g) => setForm((p) => ({
    ...p,
    financial_goals: p.financial_goals.includes(g)
      ? p.financial_goals.filter((x) => x !== g)
      : [...p.financial_goals, g],
  }));

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...form,
        age:                      parseInt(form.age),
        monthly_income_inr:       parseFloat(form.monthly_income_inr),
        monthly_expenses_inr:     parseFloat(form.monthly_expenses_inr),
        existing_investments_inr: parseFloat(form.existing_investments_inr || 0),
        tax_bracket_pct:          parseFloat(form.tax_bracket_pct),
      };
      const profile = await profileApi.create(payload);
      let risk = null;
      try {
        const r = await profileApi.analyzeRisk(payload.user_id);
        risk = r.analysis;
      } catch (_) {}
      setResult({ profile, risk });
      onProfileSaved && onProfileSaved(profile);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 max-w-lg mx-auto">
        <div className="text-center mb-5">
          <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <ShieldCheck size={28} className="text-emerald-600" />
          </div>
          <h3 className="font-bold text-gray-900 text-lg">Profile Created!</h3>
          <p className="text-sm text-gray-400">Your risk profile has been saved</p>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-5">
          {[
            ["Risk Score",      result.profile.risk_score + "/100"],
            ["Savings Rate",    (result.profile.savings_rate_pct || 0).toFixed(1) + "%"],
            ["Monthly Surplus", "Rs." + Math.round(result.profile.investable_surplus_inr || 0).toLocaleString("en-IN")],
            ["Horizon",         (result.profile.investment_horizon || "").toUpperCase()],
          ].map(([label, value]) => (
            <div key={label} className="bg-gray-50 rounded-xl p-3">
              <p className="text-xs text-gray-400">{label}</p>
              <p className="font-bold text-gray-900 mt-0.5">{value}</p>
            </div>
          ))}
        </div>

        {result.risk && (
          <div className="bg-blue-50 rounded-xl p-4 text-sm text-blue-800 leading-relaxed whitespace-pre-wrap mb-4">
            {result.risk}
          </div>
        )}

        <button onClick={() => { setResult(null); setStep(0); }}
          className="w-full border border-gray-200 rounded-xl py-2.5 text-sm text-gray-600 hover:bg-gray-50">
          Update Profile
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto">
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <div className="text-center mb-4">
          <h3 className="font-bold text-gray-900 text-lg">{STEPS[step].title}</h3>
          <p className="text-xs text-gray-400 mt-0.5">Step {step + 1} of {STEPS.length}</p>
        </div>

        <Step current={step} total={STEPS.length} />

        {/* Step 0 - Basics */}
        {step === 0 && (
          <div className="space-y-4">
            <div>
              <label className={lbl}>Your Age</label>
              <input type="number" value={form.age} onChange={set("age")}
                placeholder="e.g. 28" min="18" max="75" className={inp} />
            </div>
            <div>
              <label className={lbl}>Tax Bracket</label>
              <select value={form.tax_bracket_pct} onChange={set("tax_bracket_pct")} className={inp}>
                <option value="0">No Income Tax</option>
                <option value="5">5% slab</option>
                <option value="20">20% slab</option>
                <option value="30">30% slab</option>
              </select>
            </div>
          </div>
        )}

        {/* Step 1 - Finances */}
        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className={lbl}>Monthly Income (Rs.)</label>
              <input type="number" value={form.monthly_income_inr} onChange={set("monthly_income_inr")}
                placeholder="e.g. 75000" className={inp} />
            </div>
            <div>
              <label className={lbl}>Monthly Expenses (Rs.)</label>
              <input type="number" value={form.monthly_expenses_inr} onChange={set("monthly_expenses_inr")}
                placeholder="e.g. 50000" className={inp} />
            </div>
            <div>
              <label className={lbl}>Existing 80C Investments (Rs.)</label>
              <input type="number" value={form.existing_investments_inr} onChange={set("existing_investments_inr")}
                placeholder="e.g. 72000 (EPF + LIC)" className={inp} />
            </div>
          </div>
        )}

        {/* Step 2 - Goals */}
        {step === 2 && (
          <div className="space-y-4">
            <div>
              <label className={lbl}>Risk Appetite</label>
              <div className="grid grid-cols-3 gap-2">
                {["low","medium","high"].map((r) => (
                  <button key={r} onClick={() => setForm((p) => ({ ...p, risk_appetite: r }))}
                    className={"py-2.5 text-sm rounded-xl border font-medium transition-all " +
                      (form.risk_appetite === r ? "bg-blue-600 text-white border-blue-600" : "border-gray-200 text-gray-600 hover:border-blue-300")}>
                    {r.charAt(0).toUpperCase() + r.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className={lbl}>Investment Horizon</label>
              <div className="grid grid-cols-3 gap-2">
                {[["short","< 1 Yr"],["medium","1-3 Yrs"],["long","3+ Yrs"]].map(([v, l]) => (
                  <button key={v} onClick={() => setForm((p) => ({ ...p, investment_horizon: v }))}
                    className={"py-2.5 text-sm rounded-xl border font-medium transition-all " +
                      (form.investment_horizon === v ? "bg-blue-600 text-white border-blue-600" : "border-gray-200 text-gray-600 hover:border-blue-300")}>
                    {l}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className={lbl}>Financial Goals</label>
              <div className="flex flex-wrap gap-2">
                {GOALS.map((g) => (
                  <button key={g} onClick={() => toggleGoal(g)}
                    className={"px-3 py-1.5 text-xs rounded-full border transition-all " +
                      (form.financial_goals.includes(g) ? "bg-emerald-600 text-white border-emerald-600" : "border-gray-200 text-gray-600 hover:border-emerald-300")}>
                    {g}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {error && <div className="mt-3 text-xs text-red-600 bg-red-50 rounded-xl px-3 py-2">{error}</div>}

        <div className="flex gap-3 mt-6">
          {step > 0 && (
            <button onClick={() => setStep((s) => s - 1)}
              className="flex-1 border border-gray-200 rounded-xl py-2.5 text-sm text-gray-600
                         flex items-center justify-center gap-1 hover:bg-gray-50">
              <ChevronLeft size={14} /> Back
            </button>
          )}
          {step < STEPS.length - 1 ? (
            <button onClick={() => setStep((s) => s + 1)}
              className="flex-1 bg-blue-600 text-white rounded-xl py-2.5 text-sm font-medium
                         flex items-center justify-center gap-1 hover:bg-blue-700">
              Next <ChevronRight size={14} />
            </button>
          ) : (
            <button onClick={submit} disabled={loading}
              className="flex-1 bg-emerald-600 text-white rounded-xl py-2.5 text-sm font-medium
                         hover:bg-emerald-700 disabled:opacity-50">
              {loading ? "Saving..." : "Create Profile"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}