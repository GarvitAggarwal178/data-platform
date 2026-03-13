from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from database import get_db
from models import DimOrganization, FactTransaction

router = APIRouter(tags=["organizations"])


@router.get("/organizations")
async def get_organizations(
    sector: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(
            DimOrganization.org_name,
            DimOrganization.org_type,
            DimOrganization.sector,
            DimOrganization.registration_no.label("source"),
            func.sum(FactTransaction.amount_usd).label("total_funding"),
            func.count(FactTransaction.transaction_id).label("project_count"),
        )
        .join(FactTransaction, DimOrganization.org_id == FactTransaction.org_id, isouter=True)
        .group_by(
            DimOrganization.org_name,
            DimOrganization.org_type,
            DimOrganization.sector,
            DimOrganization.registration_no,
        )
        .order_by(func.sum(FactTransaction.amount_usd).desc())
    )

    if sector:
        query = query.where(DimOrganization.sector.ilike(f"%{sector}%"))

    result = await db.execute(query)
    rows = result.mappings().all()
    return {"data": [dict(row) for row in rows]}