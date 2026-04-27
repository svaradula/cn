/**
 * Dashboard.jsx - Budget analysis with charts.
 */
import { useState } from "react";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { Wallet, TrendingUp, PiggyBank, AlertTriangle, ChevronRight } from "lucide-react";
import { useBudgetAnalysis } from "../hooks/useFunds";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"];

function StatCard({ icon: Icon, label, value, sub, color }) {
  const colors = {
    blue:  "bg-blue-50 text-blue-600",
    green: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
  };
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
      <div className="flex items-start justify-between mb-2">
        <span className="text-xs text-gray-400 font-medium">{label}</span>
        <div className={"w-8 h-8 rounded-lg flex items-center justify-center " + (colors[color] || colors.blue)}>
          <Icon size={14} />
        </div>
      </div>
      <p className="text-xl font-bold text-gray-900">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

const inp = "w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500";

function BudgetForm({ onAnalyze, loading }) {
  const [form, setForm] = useState({
    user_id: "demo_user",
    monthly_income_inr: "",
    monthly_expenses_inr: "",
    existing_investments_inr: "",
    tax_bracket_pct: "30",
  });
  const set = (k) => (e) => setForm((p) => ({ ...p, [k]: e.target.value }));

  const submit = (e) => {
    e.preventDefault();
    onAnalyze({
      user_id: form.user_id,
      monthly_income_inr:       parseFloat(form.monthly_income_inr),
      monthly_expenses_inr:     parseFloat(form.monthly_expenses_inr),
      existing_investments_inr: parseFloat(form.existing_investments_inr || 0),
      tax_bracket_pct:          parseFloat(form.tax_bracket_pct),
    });
  };

  return (
    <form onSubmit={submit} className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
      <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Wallet size={16} className="text-blue-500" /> Budget Analysis
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <div>
          <label className="text-xs text-gray-500 block mb-1">Monthly Income (Rs.)</label>
          <input type="number" value={form.monthly_income_inr} onChange={set("monthly_income_inr")}
            placeholder="e.g. 80000" required className={inp} />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Monthly Expenses (Rs.)</label>
          <input type="number" value={form.monthly_expenses_inr} onChange={set("monthly_expenses_inr")}
            placeholder="e.g. 55000" required className={inp} />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Existing 80C Investments (Rs.)</label>
          <input type="number" value={form.existing_investments_inr} onChange={set("existing_investments_inr")}
            placeholder="e.g. 50000" className={inp} />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Tax Bracket (%)</label>
          <select value={form.tax_bracket_pct} onChange={set("tax_bracket_pct")} className={inp}>
            <option value="0">0% - No tax</option>
            <option value="5">5%</option>
            <option value="20">20%</option>
            <option value="30">30%</option>
          </select>
        </div>
      </div>
      <button type="submit" disabled={loading}
        className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm
                   hover:bg-blue-700 disabled:opacity-50 transition-colors">
        {loading ? "Analyzing..." : "Analyze My Budget"}
      </button>
    </form>
  );
}

function BudgetResult({ result }) {
  const pieData = [
    { name: "Expenses", value: Math.max(0, result.monthly_expenses) },
    { name: "Savings",  value: Math.max(0, result.monthly_savings)  },
  ];
  const barData = [
    { name: "Savings", actual: Math.max(0, result.monthly_savings), target: result.recommended_savings_inr },
    { name: "Expenses",actual: Math.max(0, result.monthly_expenses),target: result.recommended_needs_inr + result.recommended_wants_inr },
  ];
  const rate = result.savings_rate_pct || 0;
  const rateColor = rate >= 20 ? "green" : rate >= 10 ? "amber" : "blue";

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatCard icon={Wallet}     label="Monthly Income"  value={"Rs." + Math.round(result.monthly_income).toLocaleString("en-IN")}  color="blue" />
        <StatCard icon={PiggyBank}  label="Monthly Savings" value={"Rs." + Math.round(result.monthly_savings).toLocaleString("en-IN")} color={rateColor} sub={rate.toFixed(1) + "% savings rate"} />
        <StatCard icon={TrendingUp} label="Tax Saving Opp." value={"Rs." + Math.round(result.tax_saving_opportunity_inr || 0).toLocaleString("en-IN")} color="green" sub="Remaining 80C limit" />
        <StatCard icon={PiggyBank}  label="Emergency Fund"  value={"Rs." + Math.round(result.emergency_fund_target_inr || 0).toLocaleString("en-IN")} color="amber" sub="6-month target" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Income Breakdown</h4>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value">
                {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Pie>
              <Tooltip formatter={(v) => "Rs." + Math.round(v).toLocaleString("en-IN")} />
              <Legend iconSize={8} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Actual vs Recommended</h4>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={barData} barGap={4}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => "Rs." + Math.round(v / 1000) + "k"} />
              <Tooltip formatter={(v) => "Rs." + Math.round(v).toLocaleString("en-IN")} />
              <Legend iconSize={8} />
              <Bar dataKey="actual" name="Actual"       fill="#3b82f6" radius={[3,3,0,0]} />
              <Bar dataKey="target" name="Recommended"  fill="#10b981" radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {result.ai_insights && (
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <TrendingUp size={14} className="text-blue-500" /> AI Insights
          </h4>
          <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{result.ai_insights}</div>
        </div>
      )}

      {result.suggestions && result.suggestions.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Action Items</h4>
          <div className="space-y-2">
            {result.suggestions.map((s, i) => (
              <div key={i} className="flex gap-2 text-sm text-gray-700 bg-gray-50 rounded-lg p-3">
                <ChevronRight size={14} className="text-blue-400 flex-shrink-0 mt-0.5" />
                <span>{s}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const { result, loading, error, analyze } = useBudgetAnalysis();
  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-bold text-gray-900">Budget Dashboard</h2>
        <p className="text-sm text-gray-400">AI-powered analysis of your income, expenses, and savings</p>
      </div>
      <BudgetForm onAnalyze={analyze} loading={loading} />
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-600 flex items-center gap-2">
          <AlertTriangle size={14} /> {error}
        </div>
      )}
      {result && <BudgetResult result={result} />}
    </div>
  );
}