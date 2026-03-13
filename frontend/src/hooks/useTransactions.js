import { useQuery } from "@tanstack/react-query"
import client from "../api/client"

export function useTransactions(filters = {}) {
  // remove keys where value is empty string or null
  // so we don't send ?country=&year= to the API
  const cleanFilters = Object.fromEntries(
    Object.entries(filters).filter(([_, v]) => v !== "" && v !== null)
  )

  return useQuery({
    // queryKey includes filters — if filters change, React Query
    // treats it as a different query and fetches fresh data
    queryKey: ["transactions", cleanFilters],
    queryFn: () =>
      client.get("/api/v1/transactions", { params: cleanFilters })
        .then(res => res.data),
  })
}