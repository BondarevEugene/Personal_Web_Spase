"""Railway project inventory contract, handling errors without credentials."""
import httpx
import pytest

from automation import railway_inventory


def test_projects_graphql_schema_uses_documented_fields():
    assert "projects {" in railway_inventory.PROJECTS_QUERY
    assert "services { edges" in railway_inventory.PROJECTS_QUERY
    assert "environments { edges" in railway_inventory.PROJECTS_QUERY


def test_read_only_inventory_sanitizes_output(monkeypatch):
    captured = {}
    class FakeResponse:
        content = b'{}'
        def raise_for_status(self):
            return None
        def json(self):
            return {"data": {"projects": {"edges": [
                {"node": {"id": "proj-1", "name": "Example",
                          "services": {"edges": [
                              {"node": {"id": "svc-1", "name": "Worker"}}]},
                          "environments": {"edges": [
                              {"node": {"id": "env-1", "name": "production"}}]}}}
            ]}}}
    class Client:
        def __init__(self, **kwargs):
            assert kwargs["follow_redirects"] is False
            assert kwargs["trust_env"] is False
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def post(self, url, json, headers):
            captured["url"] = url
            captured["query"] = json["query"]
            assert headers["Authorization"] == "Bearer test-secret"
            return FakeResponse()
    monkeypatch.setattr(railway_inventory.httpx, "Client", Client)
    result = railway_inventory.list_projects("test-secret")
    assert captured["url"] == "https://backboard.railway.com/graphql/v2"
    assert len(result) == 1
    assert result[0]["services"][0]["name"] == "Worker"
    assert "test-secret" not in str(result)


def test_graphql_error_rejected_even_when_http_200(monkeypatch):
    class Response:
        content = b'{}'
        def raise_for_status(self):
            pass
        def json(self):
            return {"errors": [{"message": "Access denied"}], "data": None}
    class Client:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, *args, **kwargs):
            return Response()
    monkeypatch.setattr(railway_inventory.httpx, "Client", Client)
    with pytest.raises(railway_inventory.RailwayReadError):
        railway_inventory.list_projects("token")


def test_missing_access_token_never_requests_railway():
    with pytest.raises(railway_inventory.RailwayReadError):
        railway_inventory.list_projects("")
