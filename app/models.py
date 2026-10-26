import enum
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ToolStatus(str, enum.Enum):
    AVAILABLE = "Available"
    RESERVED = "Reserved"
    ON_LOAN = "On loan"
    IN_REPAIR = "In repair"


class ReservationStatus(str, enum.Enum):
    ACTIVE = "Active"


def _enum(cls: type[enum.Enum]) -> Enum:
    # Persist the human-readable value ("On loan"), not the member name.
    return Enum(cls, values_callable=lambda e: [m.value for m in e], native_enum=False)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))
    asset_tag: Mapped[str] = mapped_column(String(50), unique=True)
    status: Mapped[ToolStatus] = mapped_column(_enum(ToolStatus), default=ToolStatus.AVAILABLE)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id"), index=True)
    pickup_day: Mapped[date] = mapped_column(Date)
    status: Mapped[ReservationStatus] = mapped_column(
        _enum(ReservationStatus), default=ReservationStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class WaitlistEntry(Base):
    """A member queued for a tool that is On loan; FIFO order is by ``id``."""

    __tablename__ = "waitlist_entries"
    __table_args__ = (UniqueConstraint("tool_id", "member_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id"), index=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
