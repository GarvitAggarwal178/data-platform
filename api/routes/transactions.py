from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from database import get_db
from models import FactTransaction, DimGeography, DimOrganization, DimTime, DimProgram

router = APIRouter(tags=["transactions"])


@router.get("/transactions")
async def get_transactions(
    country:    Optional[str] = Query(None, description="Filter by country name"),
    sector:     Optional[str] = Query(None, description="Filter by sector e.g. Education"),
    year:       Optional[int] = Query(None, description="Filter by year"),
    min_amount: Optional[float] = Query(None, description="Minimum transaction amount USD"),
    max_amount: Optional[float] = Query(None, description="Maximum transaction amount USD"),
    source:     Optional[str] = Query(None, description="Data source: World Bank, OECD, SEC EDGAR"),
    limit:      int = Query(100, le=1000),
    offset:     int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    # Start with a base query that joins all dimension tables
    # This is the star schema join — one fact table, four dimension lookups
    query = (
        select(
            FactTransaction.transaction_id,
            FactTransaction.amount_usd,
            FactTransaction.currency,
            FactTransaction.status,
            FactTransaction.raw_source_id,
            DimGeography.country,
            DimGeography.region,
            DimOrganization.org_name,
            DimOrganization.sector,
            DimTime.full_date,
            DimTime.year,
            DimTime.quarter,
            DimProgram.program_name,
            DimProgram.source,
        )
        .join(DimGeography, FactTransaction.geo_id == DimGeography.geo_id, isouter=True)
        .join(DimOrganization, FactTransaction.org_id == DimOrganization.org_id, isouter=True)
        .join(DimTime, FactTransaction.time_id == DimTime.time_id, isouter=True)
        .join(DimProgram, FactTransaction.program_id == DimProgram.program_id, isouter=True)
    )

    # Each filter is applied only if the parameter was actually passed
    # This is dynamic query building — one endpoint handles all filter combinations
    if country:
        query = query.where(DimGeography.country.ilike(f"%{country}%"))
    if sector:
        query = query.where(DimOrganization.sector.ilike(f"%{sector}%"))
    if year:
        query = query.where(DimTime.year == year)
    if min_amount:
        query = query.where(FactTransaction.amount_usd >= min_amount)
    if max_amount:
        query = query.where(FactTransaction.amount_usd <= max_amount)
    if source:
        query = query.where(DimProgram.source.ilike(f"%{source}%"))

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    rows = result.mappings().all()

    return {"data": [dict(row) for row in rows], "count": len(rows)}


@router.get("/transactions/summary")
async def get_summary(
    country: Optional[str] = Query(None),
    year:    Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # Aggregation query — total spend by sector
    # This is what the dashboard charts will call
    query = (
        select(
            DimOrganization.sector,
            DimProgram.source,
            DimTime.year,
            func.sum(FactTransaction.amount_usd).label("total_amount"),
            func.count(FactTransaction.transaction_id).label("transaction_count"),
        )
        .join(DimGeography, FactTransaction.geo_id == DimGeography.geo_id, isouter=True)
        .join(DimOrganization, FactTransaction.org_id == DimOrganization.org_id, isouter=True)
        .join(DimTime, FactTransaction.time_id == DimTime.time_id, isouter=True)
        .join(DimProgram, FactTransaction.program_id == DimProgram.program_id, isouter=True)
        .group_by(DimOrganization.sector, DimProgram.source, DimTime.year)
        .order_by(func.sum(FactTransaction.amount_usd).desc())
    )

    if country:
        query = query.where(DimGeography.country.ilike(f"%{country}%"))
    if year:
        query = query.where(DimTime.year == year)

    result = await db.execute(query)
    rows = result.mappings().all()

    return {"data": [dict(row) for row in rows]}