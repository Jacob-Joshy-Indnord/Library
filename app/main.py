from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app import reservations, waitlist
from app.db import Base, engine, get_session
from app.schemas import ReservationCreate, ReservationOut, WaitlistEntryOut, WaitlistJoin


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="ToolShare", lifespan=lifespan)


def get_today() -> date:
    """Library-local 'today'; overridable in tests."""
    return date.today()


@app.post(
    "/reservations",
    response_model=ReservationOut,
    status_code=status.HTTP_201_CREATED,
    responses={404: {}, 409: {}, 422: {}},
)
def create_reservation(
    payload: ReservationCreate,
    session: Session = Depends(get_session),
    today: date = Depends(get_today),
) -> ReservationOut:
    try:
        reservation = reservations.create_reservation(
            session,
            member_id=payload.member_id,
            tool_id=payload.tool_id,
            pickup_day=payload.pickup_day,
            today=today,
        )
    except reservations.NotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except reservations.InvalidPickupDay as e:
        raise HTTPException(422, str(e))
    except reservations.ToolUnavailable as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return ReservationOut.model_validate(reservation)


def _entry_out(entry, position: int) -> WaitlistEntryOut:
    return WaitlistEntryOut(
        id=entry.id,
        tool_id=entry.tool_id,
        member_id=entry.member_id,
        position=position,
        created_at=entry.created_at,
    )


@app.post(
    "/tools/{tool_id}/waitlist",
    response_model=WaitlistEntryOut,
    status_code=status.HTTP_201_CREATED,
    responses={404: {}, 409: {}},
)
def join_waitlist(
    tool_id: int, payload: WaitlistJoin, session: Session = Depends(get_session)
) -> WaitlistEntryOut:
    try:
        entry, position = waitlist.join_waitlist(
            session, tool_id=tool_id, member_id=payload.member_id
        )
    except waitlist.NotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    except (waitlist.ToolNotOnLoan, waitlist.AlreadyWaiting) as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return _entry_out(entry, position)


@app.get("/tools/{tool_id}/waitlist", response_model=list[WaitlistEntryOut], responses={404: {}})
def get_waitlist(tool_id: int, session: Session = Depends(get_session)) -> list[WaitlistEntryOut]:
    try:
        entries = waitlist.list_entries(session, tool_id)
    except waitlist.NotFound as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    return [_entry_out(e, i) for i, e in enumerate(entries, start=1)]
