"""No anonymous access or ID guessing for project overview."""
from fastapi.testclient import TestClient

from server import app

client = TestClient(app)


def test_anonymous_view_is_forbidden():
    response = client.get("/account/graph-project/00000000-0000-0000-0000-000000000001")
    assert response.status_code == 401


def test_invalid_identifier_is_not_exposed_to_anonymous_clients():
    response = client.get("/account/graph-project/not-a-uuid")
    assert response.status_code == 401
