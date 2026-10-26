# ToolShare

Neighbourhood tool library service (FastAPI + SQLAlchemy). Spec: `openspec/`.

## Run tests

    python -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/pytest

`DATABASE_URL` selects the database (default: local SQLite file; use a
`postgresql+psycopg://...` URL in production).

## API

`POST /reservations` `{member_id, tool_id, pickup_day}` — reserve an Available
tool for a pickup day from today through today + 7 days (inclusive). On success
returns 201 and sets the tool status to Reserved.
Errors: 422 pickup day in the past or > 7 days out; 409 tool not Available;
404 unknown member/tool.
