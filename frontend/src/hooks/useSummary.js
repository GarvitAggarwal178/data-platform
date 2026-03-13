import { useQuery } from "@tanstack/react-query"
import client from "../api/client"

export function useSummary(filters = {}) {
  const cleanFilters = Object.fromEntries(
    Object.entries(filters).filter(([_, v]) => v !== "" && v !== null)
  )

  return useQuery({
    queryKey: ["summary", cleanFilters],
    queryFn: () =>
      client.get("/api/v1/transactions/summary", { params: cleanFilters })
        .then(res => res.data),
  })
}