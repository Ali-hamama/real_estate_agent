"""SQLAlchemy table definitions for data/processed/processed_data.csv.

Column names match the CSV so each row maps directly to a transaction. CSV
imports should convert empty strings to None, has_parking's 0/1 values to
booleans, ISO dates to date objects, and numeric values to Decimal objects.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Numeric, String, Text, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared metadata for creating the application's tables."""


class Transaction(Base):
    """A Dubai property transaction from the processed dataset."""

    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_area_name_transaction_date", "area_name", "rooms", "transaction_date"),
    )

    transaction_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    area_name: Mapped[str] = mapped_column(Text)
    building_name: Mapped[str | None] = mapped_column(Text)
    has_parking: Mapped[bool] = mapped_column(Boolean)
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    nearest_landmark: Mapped[str | None] = mapped_column(Text)
    nearest_mall: Mapped[str | None] = mapped_column(Text)
    nearest_metro: Mapped[str | None] = mapped_column(Text)
    transaction_group: Mapped[str] = mapped_column(Text)
    property_sub_type: Mapped[str | None] = mapped_column(Text)
    property_type: Mapped[str] = mapped_column(Text)
    rooms: Mapped[str | None] = mapped_column(Text)
    area: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    registration_type: Mapped[str] = mapped_column(Text)
    master_project: Mapped[str | None] = mapped_column(Text)
