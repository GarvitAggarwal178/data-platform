from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import DimGeography, FactTransaction

router = APIRouter(tags=["geography"])


@router.get("/geography/countries")
async def get_countries(db: AsyncSession = Depends(get_db)):
    query = (
        select(
            DimGeography.country,
            DimGeography.region,
            DimGeography.iso_code,
            func.count(FactTransaction.transaction_id).label("transaction_count"),
            func.sum(FactTransaction.amount_usd).label("total_amount"),
        )
        .join(FactTransaction, DimGeography.geo_id == FactTransaction.geo_id, isouter=True)
        .group_by(DimGeography.country, DimGeography.region, DimGeography.iso_code)
        .order_by(func.sum(FactTransaction.amount_usd).desc())
    )

    result = await db.execute(query)
    rows = result.mappings().all()
    return {"data": [dict(row) for row in rows]}