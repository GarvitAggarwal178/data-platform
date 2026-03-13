export function Filters({ filters, onChange, countries }) {
  const sectors = ["Education", "Health", "Infrastructure", "Agriculture", "Development Assistance", "Nonprofit / Grant"]

  return (
    <div className="flex flex-wrap gap-3 bg-white p-4 rounded-xl shadow-sm border border-slate-100">
      <select
        className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={filters.country || ""}
        onChange={e => onChange({ ...filters, country: e.target.value })}
      >
        <option value="">All Countries</option>
        {countries?.data?.map(c => (
          <option key={c.country} value={c.country}>{c.country}</option>
        ))}
      </select>

      <select
        className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={filters.sector || ""}
        onChange={e => onChange({ ...filters, sector: e.target.value })}
      >
        <option value="">All Sectors</option>
        {sectors.map(s => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>

      <select
        className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={filters.year || ""}
        onChange={e => onChange({ ...filters, year: e.target.value })}
      >
        <option value="">All Years</option>
        {[2024, 2023, 2022, 2021, 2020].map(y => (
          <option key={y} value={y}>{y}</option>
        ))}
      </select>

      <select
        className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        value={filters.source || ""}
        onChange={e => onChange({ ...filters, source: e.target.value })}
      >
        <option value="">All Sources</option>
        <option value="World Bank">World Bank</option>
        <option value="OECD">OECD</option>
        <option value="SEC EDGAR">SEC EDGAR</option>
      </select>

      {/* clear all filters */}
      {Object.values(filters).some(v => v !== "") && (
        <button
          className="text-sm text-blue-600 hover:underline px-2"
          onClick={() => onChange({})}
        >
          Clear filters
        </button>
      )}
    </div>
  )
}