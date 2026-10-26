"""Reservation creation (spec: Reservations / Create reservation for pickup day)."""
from datetime import date, timedelta

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Member, Reservation, Tool, ToolStatus

MAX_DAYS_AHEAD = 7


class ReservationError(Exception):
    """Base class for domain errors raised while creating a reservation."""


class NotFound(ReservationError):
    pass


class InvalidPickupDay(ReservationError):
    pass


class ToolUnavailable(ReservationError):
    pass


def validate_pickup_day(pickup_day: date, today: date) -> None:
    """Pickup day must be between today and today + 7 days, inclusive."""
    if pickup_day < today:
        raise InvalidPickupDay("Pickup day cannot be in the past")
    if pickup_day > today + timedelta(days=MAX_DAYS_AHEAD):
        raise InvalidPickupDay(f"Pickup day must be within the next {MAX_DAYS_AHEAD} days")


def create_reservation(
    session: Session, *, member_id: int, tool_id: int, pickup_day: date, today: date
) -> Reservation:
    validate_pickup_day(pickup_day, today)

    if session.get(Member, member_id) is None:
        raise NotFound(f"Member {member_id} not found")
    if session.get(Tool, tool_id) is None:
        raise NotFound(f"Tool {tool_id} not found")

    # Compare-and-set: only flips the status if the tool is still Available, so
    # two concurrent requests cannot both reserve the same tool.
    result = session.execute(
        update(Tool)
        .where(Tool.id == tool_id, Tool.status == ToolStatus.AVAILABLE)
        .values(status=ToolStatus.RESERVED)
        .execution_options(synchronize_session="fetch")
    )
    if result.rowcount != 1:
        session.rollback()
        raise ToolUnavailable(f"Tool {tool_id} is not available for reservation")

    reservation = Reservation(member_id=member_id, tool_id=tool_id, pickup_day=pickup_day)
    session.add(reservation)
    session.commit()
    return reservation
