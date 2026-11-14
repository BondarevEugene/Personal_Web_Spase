"""Legacy administration URLs redirect to current, protected OmniFactory tools.

The old templates contained hardcoded uptime, CPU, and imaginary bot states.
They are intentionally not served as real administrative dashboards.
"""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/admin", tags=["Administration legacy aliases"])

DESTINATIONS = {
    "/": "/bots/lab",
    "/dashboard": "/bots/lab",
    "/projects": "/projects",
    "/builder": "/architect",
    "/robotization": "/automation/studio",
    "/techkillers": "/techkillers",
}


@router.get("/{path:path}", include_in_schema=False)
async def legacy_admin_alias(path: str):
    path = "/" + path.strip("/") if path else "/"
    target = DESTINATIONS.get(path)
    if target is None:
        return RedirectResponse("/bots/lab", status_code=307)
    return RedirectResponse(target, status_code=307)
