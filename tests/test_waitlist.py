"""Spec: Reservations / Join tool waiting list (task-wMd0fV1wrng)."""
import pytest

from app.models import Member, Tool, ToolStatus, WaitlistEntry


def join(client, tool_id, member_id):
    return client.post(f"/tools/{tool_id}/waitlist", json={"member_id": member_id})


# Scenario: Member added to waiting list
def test_member_added_to_waiting_list_for_on_loan_tool(client, session, member, make_tool):
    tool = make_tool(status=ToolStatus.ON_LOAN)

    resp = join(client, tool.id, member.id)

    assert resp.status_code == 201
    body = resp.json()
    assert body["tool_id"] == tool.id
    assert body["member_id"] == member.id
    assert body["position"] == 1
    entries = session.query(WaitlistEntry).filter_by(tool_id=tool.id).all()
    assert [e.member_id for e in entries] == [member.id]
    # Joining the list does not change the tool's status.
    assert session.get(Tool, tool.id).status == ToolStatus.ON_LOAN


def test_waiting_list_preserves_join_order(client, session, member, make_tool):
    tool = make_tool(status=ToolStatus.ON_LOAN)
    other = Member(name="Grace")
    session.add(other)
    session.commit()

    assert join(client, tool.id, member.id).json()["position"] == 1
    assert join(client, tool.id, other.id).json()["position"] == 2

    resp = client.get(f"/tools/{tool.id}/waitlist")
    assert resp.status_code == 200
    assert [e["member_id"] for e in resp.json()] == [member.id, other.id]
    assert [e["position"] for e in resp.json()] == [1, 2]


@pytest.mark.parametrize(
    "status", [ToolStatus.AVAILABLE, ToolStatus.RESERVED, ToolStatus.IN_REPAIR]
)
def test_tool_not_on_loan_rejected(client, session, member, make_tool, status):
    tool = make_tool(status=status)

    resp = join(client, tool.id, member.id)

    assert resp.status_code == 409
    assert session.query(WaitlistEntry).count() == 0


def test_member_cannot_join_same_waiting_list_twice(client, session, member, make_tool):
    tool = make_tool(status=ToolStatus.ON_LOAN)
    assert join(client, tool.id, member.id).status_code == 201

    resp = join(client, tool.id, member.id)

    assert resp.status_code == 409
    assert session.query(WaitlistEntry).count() == 1


def test_unknown_tool_or_member_returns_404(client, member, make_tool):
    tool = make_tool(status=ToolStatus.ON_LOAN)
    assert join(client, 9999, member.id).status_code == 404
    assert join(client, tool.id, 9999).status_code == 404
    assert client.get("/tools/9999/waitlist").status_code == 404
