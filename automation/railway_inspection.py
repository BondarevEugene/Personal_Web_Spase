"""Railway BYOC binding verification and read-only live deployment status.

Use only fixed GraphQL queries and account-scoped OAuth tokens. A service
instance status is not a bot healthcheck; both must be verified before
reporting successful publication.
"""
from __future__ import annotations

import re

import httpx

GRAPHQL = "https://backboard.railway.com/graphql/v2"
PROJECT = """query OmnifactoryProject($id: String!) {
  project(id: $id) {
    id name
    services { edges { node { id name } } }
    environments { edges { node { id name } } }
  }
}"""
SERVICE_INSTANCE = """query OmnifactoryServiceInstance($serviceId: String!, $environmentId: String!) {
  serviceInstance(serviceId: $serviceId, environmentId: $environmentId) {
    id serviceName healthcheckPath region numReplicas
    latestDeployment { id status createdAt }
  }
}"""
ID = re.compile(r"^[A-Za-z0-9_-]{5,100}$")


class RailwayInspectError(Exception):
    pass


def _query(token: str, query: str, variables: dict) -> dict:
    if not isinstance(token, str) or not token:
        raise RailwayInspectError("Connection token unavailable")
    try:
        with httpx.Client(timeout=10, follow_redirects=False, trust_env=False) as client:
            with client.stream(
                "POST", GRAPHQL, json={"query": query, "variables": variables},
                headers={"Authorization": "Bearer " + token,
                         "Accept": "application/json"},
            ) as response:
                response.raise_for_status()
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 128_000:
                        raise RailwayInspectError("Provider response too large")
            payload = __import__("json").loads(data)
    except (httpx.HTTPError, ValueError) as exc:
        raise RailwayInspectError("Railway inspection unavailable") from exc
    if not isinstance(payload, dict) or payload.get("errors") or not isinstance(payload.get("data"), dict):
        raise RailwayInspectError("Railway rejected resource inspection")
    return payload["data"]


def inspect_binding(token: str, project_id: str, service_id: str,
                    environment_id: str) -> dict:
    for value in (project_id, service_id, environment_id):
        if not ID.fullmatch(value):
            raise RailwayInspectError("Invalid provider resource identifier")
    data = _query(token, PROJECT, {"id": project_id})
    project = data.get("project")
    if not isinstance(project, dict) or project.get("id") != project_id:
        raise RailwayInspectError("Railway project not accessible to this connection")
    try:
        services = {edge["node"]["id"] for edge in project["services"]["edges"]}
        environments = {edge["node"]["id"] for edge in project["environments"]["edges"]}
    except (KeyError, TypeError, AttributeError):
        raise RailwayInspectError("Unexpected Railway resource list")
    if service_id not in services or environment_id not in environments:
        raise RailwayInspectError("Selected service/environment does not belong to this project")
    instance_data = _query(token, SERVICE_INSTANCE,
                           {"serviceId": service_id, "environmentId": environment_id})
    instance = instance_data.get("serviceInstance")
    if not isinstance(instance, dict):
        raise RailwayInspectError("Service not present in selected environment")
    deployment = instance.get("latestDeployment")
    deployment = deployment if isinstance(deployment, dict) else None
    return {
        "project": {"id": project["id"], "name": str(project.get("name", ""))[:200]},
        "service": {"id": service_id, "name": str(instance.get("serviceName", ""))[:200]},
        "environment": {"id": environment_id},
        "instance": {"id": str(instance.get("id", ""))[:100],
                     "region": str(instance.get("region") or "")[:80],
                     "replicas": instance.get("numReplicas") if isinstance(instance.get("numReplicas"), int) else None,
                     "healthcheck_configured": bool(instance.get("healthcheckPath"))},
        "deployment": ({
            "id": str(deployment.get("id", ""))[:100],
            "status": str(deployment.get("status", "UNKNOWN"))[:50],
            "created_at": deployment.get("createdAt"),
        } if deployment else None),
        "source": "railway_graphql",
        "bot_health_verified": False,
    }
