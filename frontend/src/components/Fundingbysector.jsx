import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from "recharts"

function formatBillions(value) {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  return `$${value.toLocaleString()}`
}

export default function FundingBySector({ data }) {
  // aggregate summary data by sector, summing across years
  const bySector = Object.values(
    (data || []).reduce((acc, row) => {
      const key = row.sector || "Unknown"
      if (!acc[key]) acc[key] = { sector: key, total_amount: 0 }
      acc[key].total_amount += Number(row.total_amount || 0)
      return acc
    }, {})
  ).sort((a, b) => b.total_amount - a.total_amount).slice(0, 8)

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
      <h2 className="text-base font-semibold text-slate-700 mb-4">
        Total Funding by Sector
      </h2>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={bySector} margin={{ top: 5, right: 20, left: 10, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis
            dataKey="sector"
            tick={{ fontSize: 11 }}
            angle={-35}
            textAnchor="end"
          />
          <YAxis tickFormatter={formatBillions} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(value) => formatBillions(value)} />
          <Bar dataKey="total_amount" fill="#3b82f6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}