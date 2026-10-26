"""Tool waiting list (spec: Reservations / Join tool waiting list)."""
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Member, Tool, ToolStatus, WaitlistEntry


class WaitlistError(Exception):
    """Base class for domain errors raised by waiting-list operations."""


class NotFound(WaitlistError):
    pass


class ToolNotOnLoan(WaitlistError):
    pass


class AlreadyWaiting(WaitlistError):
    pass


def list_entries(session: Session, tool_id: int) -> list[WaitlistEntry]:
    """Entries for a tool in queue order (first in, first out)."""
    if session.get(Tool, tool_id) is None:
        raise NotFound(f"Tool {tool_id} not found")
    stmt = select(WaitlistEntry).where(WaitlistEntry.tool_id == tool_id).order_by(WaitlistEntry.id)
    return list(session.scalars(stmt))


def join_waitlist(session: Session, *, tool_id: int, member_id: int) -> tuple[WaitlistEntry, int]:
    """Append the member to the tool's waiting list; returns (entry, 1-based position)."""
    tool = session.get(Tool, tool_id)
    if tool is None:
        raise NotFound(f"Tool {tool_id} not found")
    if session.get(Member, member_id) is None:
        raise NotFound(f"Member {member_id} not found")
    if tool.status != ToolStatus.ON_LOAN:
        raise ToolNotOnLoan(f"Tool {tool_id} is not on loan; reserve it instead")

    entry = WaitlistEntry(tool_id=tool_id, member_id=member_id)
    session.add(entry)
    try:
        session.commit()
    except IntegrityError:
        # Unique (tool_id, member_id) also covers concurrent duplicate joins.
        session.rollback()
        raise AlreadyWaiting(f"Member {member_id} is already on the waiting list for tool {tool_id}")

    position = session.scalar(
        select(func.count())
        .select_from(WaitlistEntry)
        .where(WaitlistEntry.tool_id == tool_id, WaitlistEntry.id <= entry.id)
    )
    return entry, position
