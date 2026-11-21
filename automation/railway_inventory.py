"""Read-only Railway GraphQL integration for connected customer accounts.

Never accepts user-supplied GraphQL. Does not provision, mutate, or deploy.
The OAuth connection owns the token; expired access requires explicit refresh.
"""
from __future__ import annotations

import httpx

API_URL = "https://backboard.railway.com/graphql/v2"
PROJECTS_QUERY = """
query OmniFactoryAccessibleProjects {
  projects {
    edges {
      node {
        id
        name
        createdAt
        services { edges { node { id name } } }
        environments { edges { node { id name } } }
      }
    }
  }
}
"""


class RailwayReadError(Exception):
    pass


def list_projects(access_token: str) -> list[dict]:
    if not isinstance(access_token, str) or not access_token:
        raise RailwayReadError("Railway access token unavailable")
    try:
        with httpx.Client(timeout=12, follow_redirects=False, trust_env=False) as client:
            response = client.post(API_URL, json={"query": PROJECTS_QUERY},
                headers={"Authorization": "Bearer " + access_token,
                         "Content-Type": "application/json", "Accept": "application/json"})
            response.raise_for_status()
            if len(response.content) > 256_000:
                raise RailwayReadError("Railway response exceeds permitted size")
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise RailwayReadError("Cannot read Railway projects; check permissions or reconnect") from exc
    if not isinstance(payload, dict) or payload.get("errors"):
        raise RailwayReadError("Railway GraphQL rejected the project query")
    try:
        edges = payload["data"]["projects"]["edges"]
        if not isinstance(edges, list) or len(edges) > 200:
            raise ValueError("Unexpected projects list")
        results = []
        for edge in edges:
            n = edge["node"]
            results.append({
                "id": str(n["id"])[:100],
                "name": str(n["name"])[:200],
                "services": [
                    {"id": str(s["node"]["id"])[:100],
                     "name": str(s["node"]["name"])[:200]}
                    for s in n.get("services", {}).get("edges", [])[:50]
                ],
                "environments": [
                    {"id": str(e["node"]["id"])[:100],
                     "name": str(e["node"]["name"])[:200]}
                    for e in n.get("environments", {}).get("edges", [])[:20]
                ],
            })
        return results
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise RailwayReadError("Unexpected Railway projects response") from exc
