export default function TransactionsTable({ data, isLoading }) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl p-8 shadow-sm border border-slate-100 text-center text-slate-400">
        Loading...
      </div>
    )
  }

  const rows = data?.data || []

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
      <div className="p-5 border-b border-slate-100">
        <h2 className="text-base font-semibold text-slate-700">
          Transactions
          <span className="ml-2 text-sm font-normal text-slate-400">
            {rows.length} records
          </span>
        </h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wide">
            <tr>
              {["Organization", "Country", "Sector", "Amount (USD)", "Year", "Source", "Status"].map(h => (
                <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {rows.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                  No records found
                </td>
              </tr>
            ) : (
              rows.map((row, i) => (
                <tr key={i} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-slate-700 max-w-[200px] truncate">
                    {row.org_name || "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{row.country || "—"}</td>
                  <td className="px-4 py-3 text-slate-600">{row.sector || "—"}</td>
                  <td className="px-4 py-3 text-slate-800 font-medium">
                    {row.amount_usd
                      ? `$${Number(row.amount_usd).toLocaleString()}`
                      : "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{row.year || "—"}</td>
                  <td className="px-4 py-3">
                    <span className="bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full">
                      {row.source || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      row.status === "disbursed"
                        ? "bg-green-50 text-green-700"
                        : "bg-slate-100 text-slate-600"
                    }`}>
                      {row.status || "—"}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}