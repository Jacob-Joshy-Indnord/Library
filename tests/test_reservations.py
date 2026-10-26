"""Spec: Reservations / Create reservation for pickup day (task-ej_GG0bdwNo)."""
from datetime import timedelta

import pytest

from app.models import Reservation, Tool, ToolStatus
from tests.conftest import TODAY


def reserve(client, member_id, tool_id, pickup_day):
    return client.post(
        "/reservations",
        json={"member_id": member_id, "tool_id": tool_id, "pickup_day": pickup_day.isoformat()},
    )


# Scenario: Reservation created for valid pickup day
@pytest.mark.parametrize("days_out", [0, 1, 7])
def test_reservation_created_and_tool_reserved(client, session, member, make_tool, days_out):
    tool = make_tool()
    pickup = TODAY + timedelta(days=days_out)

    resp = reserve(client, member.id, tool.id, pickup)

    assert resp.status_code == 201
    body = resp.json()
    assert body["tool_id"] == tool.id
    assert body["member_id"] == member.id
    assert body["pickup_day"] == pickup.isoformat()
    assert body["status"] == "Active"
    assert session.get(Tool, tool.id).status == ToolStatus.RESERVED
    assert session.query(Reservation).count() == 1


# Scenario: Pickup day beyond 7 days rejected
@pytest.mark.parametrize("days_out", [8, 30])
def test_pickup_day_beyond_seven_days_rejected(client, session, member, make_tool, days_out):
    tool = make_tool()

    resp = reserve(client, member.id, tool.id, TODAY + timedelta(days=days_out))

    assert resp.status_code == 422
    assert "7 days" in resp.json()["detail"]
    assert session.get(Tool, tool.id).status == ToolStatus.AVAILABLE
    assert session.query(Reservation).count() == 0


def test_pickup_day_in_past_rejected(client, session, member, make_tool):
    tool = make_tool()

    resp = reserve(client, member.id, tool.id, TODAY - timedelta(days=1))

    assert resp.status_code == 422
    assert session.get(Tool, tool.id).status == ToolStatus.AVAILABLE


@pytest.mark.parametrize(
    "status", [ToolStatus.RESERVED, ToolStatus.ON_LOAN, ToolStatus.IN_REPAIR]
)
def test_unavailable_tool_rejected(client, session, member, make_tool, status):
    tool = make_tool(status=status)

    resp = reserve(client, member.id, tool.id, TODAY + timedelta(days=1))

    assert resp.status_code == 409
    assert session.get(Tool, tool.id).status == status
    assert session.query(Reservation).count() == 0


def test_second_reservation_for_same_tool_rejected(client, session, member, make_tool):
    tool = make_tool()
    assert reserve(client, member.id, tool.id, TODAY + timedelta(days=2)).status_code == 201

    resp = reserve(client, member.id, tool.id, TODAY + timedelta(days=3))

    assert resp.status_code == 409
    assert session.query(Reservation).count() == 1


def test_unknown_tool_or_member_returns_404(client, member, make_tool):
    tool = make_tool()
    assert reserve(client, member.id, 9999, TODAY).status_code == 404
    assert reserve(client, 9999, tool.id, TODAY).status_code == 404
