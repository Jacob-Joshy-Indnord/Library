from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_session
from app.main import app, get_today
from app.models import Member, Tool, ToolStatus

TODAY = date(2026, 10, 26)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    yield db
    db.close()


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_today] = lambda: TODAY
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def member(session):
    m = Member(name="Ada")
    session.add(m)
    session.commit()
    return m


@pytest.fixture
def make_tool(session):
    def _make(status=ToolStatus.AVAILABLE, tag="T-001"):
        t = Tool(name="Drill", category="Power tools", asset_tag=tag, status=status)
        session.add(t)
        session.commit()
        return t

    return _make
