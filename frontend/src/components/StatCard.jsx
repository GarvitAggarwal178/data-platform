export default function StatCard({ title, value, subtitle }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
      <p className="text-sm text-slate-500 font-medium">{title}</p>
      <p className="text-3xl font-bold text-slate-800 mt-1">{value}</p>
      {subtitle && (
        <p className="text-xs text-slate-400 mt-1">{subtitle}</p>
      )}
    </div>
  )
}