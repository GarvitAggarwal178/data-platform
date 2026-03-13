from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import transactions, geography, organizations

app = FastAPI(
    title="Financial Data Platform",
    description="Query public financial data for NGOs and nonprofits",
    version="1.0.0",
)

# CORS lets the React frontend (running on localhost:3000) call this API
# Without this, browsers block cross-origin requests by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(transactions.router, prefix="/api/v1")
app.include_router(geography.router, prefix="/api/v1")
app.include_router(organizations.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}