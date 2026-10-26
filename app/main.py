from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app import reservations
from app.db import Base, engine, get_session
from app.schemas import ReservationCreate, ReservationOut


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
