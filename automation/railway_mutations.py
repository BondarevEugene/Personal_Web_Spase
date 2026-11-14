"""Railway mutation adapter.

The adapter is intentionally separate from the customer-facing API.
It can be used in an operator-controlled integration test, but the production
worker currently has NO path to invoke mutations: validated runtime images,
quoted provider spend and a verified isolation policy are not yet available.

Railway GraphQL operations documented at:
https://docs.railway.com/integrations/api/manage-projects
https://docs.railway.com/integrations/api/manage-services
"""
from __future__ import annotations

import httpx

API = "https://backboard.railway.com/graphql/v2"
PROJECT_CREATE = """mutation projectCreate($input: ProjectCreateInput!) {
  projectCreate(input: $input) { id name }
}"""
SERVICE_CREATE = """mutation serviceCreate($input: ServiceCreateInput!) {
  serviceCreate(input: $input) { id name }
}"""
SERVICE_DEPLOY = """mutation serviceInstanceDeployV2($serviceId: String!, $environmentId: String!) {
  serviceInstanceDeployV2(serviceId: $serviceId, environmentId: $environmentId)
}"""


class RailwayMutationError(Exception):
    """Sanitized, not including tokens or raw provider request bodies."""


class RailwayGraphQLAdapter:
    def __init__(self, access_token: str):
        if not access_token or len(access_token) > 8192:
            raise ValueError("Invalid access token")
        self._token = access_token

    def _mutate(self, query: str, variables: dict, result_key: str):
        try:
            with httpx.Client(timeout=15, follow_redirects=False, trust_env=False) as client:
                res = client.post(
                    API, json={"query": query, "variables": variables},
                    headers={"Authorization": "Bearer " + self._token,
                             "Accept": "application/json"})
                if len(res.content) > 65536:
                    raise RailwayMutationError("Provider response too large")
                res.raise_for_status()
                response = res.json()
        except (httpx.HTTPError, ValueError) as exc:
            # The mutation may have happened even if the response was lost.
            # NEVER automatically retry create operations after this error.
            raise RailwayMutationError("Unknown mutation outcome; reconcile manually") from exc
        if not isinstance(response, dict) or response.get("errors"):
            raise RailwayMutationError("Railway rejected mutation; inspect trace ID out of band")
        result = (response.get("data") or {}).get(result_key)
        if not result:
            raise RailwayMutationError("Railway returned no confirmed resource")
        return result

    def create_project(self, name: str) -> dict:
        return self._mutate(PROJECT_CREATE, {"input": {"name": name}}, "projectCreate")

    def create_service(self, project_id: str, name: str, *, image: str) -> dict:
        # Only operator-approved, immutable digest images are eligible.
        if "@sha256:" not in image:
            raise ValueError("Service requires an immutable image digest")
        return self._mutate(SERVICE_CREATE, {"input": {
            "projectId": project_id, "name": name,
            "source": {"image": image},
        }}, "serviceCreate")

    def deploy(self, service_id: str, environment_id: str) -> str:
        value = self._mutate(SERVICE_DEPLOY, {
            "serviceId": service_id, "environmentId": environment_id,
        }, "serviceInstanceDeployV2")
        if not isinstance(value, str):
            raise RailwayMutationError("Unexpected deployment identifier")
        return value
