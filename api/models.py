from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class DimGeography(Base):
    __tablename__ = "dim_geography"
    __table_args__ = {"schema": "warehouse"}

    geo_id   = Column(String, primary_key=True)
    country  = Column(String)
    region   = Column(String)
    state    = Column(String)
    city     = Column(String)
    iso_code = Column(String)


class DimOrganization(Base):
    __tablename__ = "dim_organization"
    __table_args__ = {"schema": "warehouse"}

    org_id          = Column(String, primary_key=True)
    org_name        = Column(String)
    org_type        = Column(String)
    sector          = Column(String)
    registration_no = Column(String)


class DimTime(Base):
    __tablename__ = "dim_time"
    __table_args__ = {"schema": "warehouse"}

    time_id    = Column(String, primary_key=True)
    full_date  = Column(Date)
    day        = Column(Integer)
    month      = Column(Integer)
    quarter    = Column(Integer)
    year       = Column(Integer)
    month_name = Column(String)


class DimProgram(Base):
    __tablename__ = "dim_program"
    __table_args__ = {"schema": "warehouse"}

    program_id   = Column(String, primary_key=True)
    program_name = Column(String)
    program_type = Column(String)
    source       = Column(String)


class FactTransaction(Base):
    __tablename__ = "fact_transactions"
    __table_args__ = {"schema": "warehouse"}

    transaction_id = Column(String, primary_key=True)
    org_id         = Column(String, ForeignKey("warehouse.dim_organization.org_id"))
    geo_id         = Column(String, ForeignKey("warehouse.dim_geography.geo_id"))
    time_id        = Column(String, ForeignKey("warehouse.dim_time.time_id"))
    program_id     = Column(String, ForeignKey("warehouse.dim_program.program_id"))
    amount_usd     = Column(Numeric)
    currency       = Column(String)
    exchange_rate  = Column(Numeric)
    status         = Column(String)
    raw_source_id  = Column(String)

    geography    = relationship("DimGeography")
    organization = relationship("DimOrganization")
    time         = relationship("DimTime")
    program      = relationship("DimProgram")