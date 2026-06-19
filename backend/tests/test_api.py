import pytest
from fastapi.testclient import TestClient

from app.seed.sample_docs import SAMPLE_REFUND_DOC


@pytest.fixture
def client():
    from app.api.main import create_app  # uses the sqlite DB bound in conftest

    app = create_app()
    with TestClient(app) as c:
        c._doc = SAMPLE_REFUND_DOC
        yield c


def test_full_flow(client):
    doc = client._doc
    cid = client.post("/companies", json={"name": "Acme Flow"}).json()["id"]
    assert client.post(f"/companies/{cid}/ingest", json={"text": doc}).json()["nodes_created"]

    gen = client.post(f"/companies/{cid}/skills/generate", json={"goal": "refund_customer"}).json()
    assert gen["name"] == "refund_customer"
    assert [i["name"] for i in gen["inputs"]] == ["customer_id"]
    sid = gen["id"]

    # auto-approve path: no human needed
    r1 = client.post(f"/skills/{sid}/execute", json={"inputs": {"customer_id": "cust_loyal"}}).json()
    assert r1["status"] == "completed"
    assert r1["outcome"] == "approve_refund"

    # human-in-the-loop path: fraud flag pauses for approval
    r2 = client.post(f"/skills/{sid}/execute", json={"inputs": {"customer_id": "cust_fraud"}}).json()
    assert r2["status"] == "pending_approval"
    done = client.post(
        f"/approvals/{r2['approval_id']}/decision",
        json={"decision": "approve", "decided_by": "fin@acme"},
    ).json()
    assert done["status"] == "completed"


def test_generate_unknown_goal_is_422(client):
    cid = client.post("/companies", json={"name": "Acme Unknown"}).json()["id"]
    client.post(f"/companies/{cid}/ingest", json={"text": client._doc})
    resp = client.post(f"/companies/{cid}/skills/generate", json={"goal": "launch_rocket"})
    assert resp.status_code == 422
