import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from "recharts"

function formatBillions(value) {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  return `$${value.toLocaleString()}`
}

export default function FundingOverTime({ data }) {
  // aggregate by year, one line per source
  const sources = [...new Set((data || []).map(r => r.source).filter(Boolean))]

  const byYear = Object.values(
    (data || []).reduce((acc, row) => {
      const year = row.year
      if (!year) return acc
      if (!acc[year]) acc[year] = { year }
      acc[year][row.source] = (acc[year][row.source] || 0) + Number(row.total_amount || 0)
      return acc
    }, {})
  ).sort((a, b) => a.year - b.year)

  const colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
      <h2 className="text-base font-semibold text-slate-700 mb-4">
        Funding Over Time by Source
      </h2>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={byYear} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="year" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={formatBillions} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(value) => formatBillions(value)} />
          <Legend />
          {sources.map((source, i) => (
            <Line
              key={source}
              type="monotone"
              dataKey={source}
              stroke={colors[i % colors.length]}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}