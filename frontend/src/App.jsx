import { useState } from "react"
import { useTransactions } from "./hooks/useTransactions"
import { useSummary } from "./hooks/useSummary"
import { useCountries } from "./hooks/useCountries"
import StatCard from "./components/StatCard"
import FundingBySector from "./components/Fundingbysector"
import FundingOverTime from "./components/FundingOverTime"
import TransactionsTable from "./components/TransactionsTable"
import { Filters } from "./components/Filters"

function formatBillions(value) {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  return `$${Number(value).toLocaleString()}`
}

export default function App() {
  const [filters, setFilters] = useState({})

  const { data: transactions, isLoading: txLoading } = useTransactions(filters)
  const { data: summary } = useSummary(filters)
  const { data: countries } = useCountries()

  const summaryRows = summary?.data || []
  const totalAmount = summaryRows.reduce((sum, r) => sum + Number(r.total_amount || 0), 0)
  const totalCount = summaryRows.reduce((sum, r) => sum + Number(r.transaction_count || 0), 0)
  const uniqueCountries = countries?.data?.length || 0

  return (
    <div className="min-h-screen bg-slate-50">
      {/* header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <h1 className="text-xl font-bold text-slate-800">
          Financial Data Platform
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Public financial data for nonprofits — World Bank · OECD · SEC EDGAR
        </p>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* stat cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            title="Total Funding"
            value={formatBillions(totalAmount)}
            subtitle="across all sources"
          />
          <StatCard
            title="Transactions"
            value={totalCount.toLocaleString()}
            subtitle="records in warehouse"
          />
          <StatCard
            title="Countries"
            value={uniqueCountries}
            subtitle="geographic coverage"
          />
        </div>

        {/* filters */}
        <Filters
          filters={filters}
          onChange={setFilters}
          countries={countries}
        />

        {/* charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FundingBySector data={summaryRows} />
          <FundingOverTime data={summaryRows} />
        </div>

        {/* table */}
        <TransactionsTable data={transactions} isLoading={txLoading} />

      </div>
    </div>
  )
}