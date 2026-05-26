import { useMemo, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { VI } from "../lib/vi";

export default function RoiCalculator() {
  const [csStaff, setCsStaff] = useState(25);
  const [salary, setSalary] = useState(450);
  const [messagesPerDay, setMessagesPerDay] = useState(8000);
  const [autoRate, setAutoRate] = useState(0.65);

  const result = useMemo(() => {
    const monthlySavings = csStaff * salary * autoRate * 0.6;
    const hoursSaved = (messagesPerDay * autoRate * 43) / 60;
    const annualRoi = monthlySavings * 12;
    return { monthlySavings, hoursSaved, annualRoi };
  }, [csStaff, salary, messagesPerDay, autoRate]);

  const chartData = [
    { name: "Tháng", value: Math.round(result.monthlySavings) },
    { name: "Năm", value: Math.round(result.annualRoi) },
  ];

  return (
    <div className="space-y-3 rounded-lg border border-slate-700 bg-slate-900/60 p-3">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">{VI.roi.title}</h2>
      <label className="block text-xs">
        {VI.roi.staff}
        <input
          type="range"
          min={5}
          max={80}
          value={csStaff}
          onChange={(e) => setCsStaff(+e.target.value)}
          className="w-full"
        />
        <span className="text-amber-300">{csStaff} người</span>
      </label>
      <label className="block text-xs">
        {VI.roi.salary}
        <input
          type="number"
          value={salary}
          onChange={(e) => setSalary(+e.target.value)}
          className="mt-1 w-full rounded bg-slate-800 px-2 py-1"
        />
      </label>
      <label className="block text-xs">
        {VI.roi.messages}
        <input
          type="number"
          value={messagesPerDay}
          onChange={(e) => setMessagesPerDay(+e.target.value)}
          className="mt-1 w-full rounded bg-slate-800 px-2 py-1"
        />
      </label>
      <label className="block text-xs">
        {VI.roi.autoRate} {(autoRate * 100).toFixed(0)}%
        <input
          type="range"
          min={0.2}
          max={0.9}
          step={0.05}
          value={autoRate}
          onChange={(e) => setAutoRate(+e.target.value)}
          className="w-full"
        />
      </label>
      <div className="text-sm text-emerald-300">
        {VI.roi.result(Math.round(result.monthlySavings), result.hoursSaved)}
      </div>
      <p className="text-[10px] text-slate-500">{VI.roi.disclaimer}</p>
      <div className="h-28">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <Tooltip contentStyle={{ background: "#1e293b", border: "none" }} />
            <Bar dataKey="value" fill="#f59e0b" radius={4} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
