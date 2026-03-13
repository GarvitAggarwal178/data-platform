import { useQuery } from "@tanstack/react-query"
import client from "../api/client"

export function useCountries() {
  return useQuery({
    queryKey: ["countries"],
    queryFn: () =>
      client.get("/api/v1/geography/countries").then(res => res.data),
    // countries list rarely changes — cache for 30 minutes
    staleTime: 30 * 60 * 1000,
  })
}