import axios from "axios"

// single axios instance — base URL comes from env var
// in development: http://localhost:8000
// in production: your Render API URL
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 10000,
})

export default client