"""Public automation discovery and safe, server-owned workflow previews."""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from omni_site.automation_flagship import (
    BY_SLUG,
    INTEGRATIONS,
    STATUS_LABELS,
    TEMPLATES,
    preview,
    template_definition,
)

router = APIRouter(tags=["Automation Flagship"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/integrations", response_class=HTMLResponse)
def integrations_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="automation_flagship.html",
        context={
            "integrations": INTEGRATIONS, "statuses": STATUS_LABELS,
            "automation_templates": TEMPLATES,
        },
    )


@router.get("/integrations/templates/{slug}")
def download_template(slug: str):
    if slug not in BY_SLUG:
        raise HTTPException(404, "Template not found")
    data = template_definition(slug).model_dump(mode="json")
    return JSONResponse(
        data,
        headers={
            "Content-Disposition": f'attachment; filename="omni-{slug}.json"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/integrations/preview/{slug}")
def preview_template(slug: str):
    if slug not in BY_SLUG:
        raise HTTPException(404, "Template not found")
    return JSONResponse(
        preview(slug),
        headers={"Cache-Control": "no-store"},
    )
