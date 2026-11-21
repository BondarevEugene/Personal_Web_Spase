"""End-to-end contracts for the four public Experience Lab scenarios."""

import pytest

from omni_site.blueprint_specification import compile_specification
from omni_site.blueprint_studio import SECTORS, make_blueprint
from omni_site.solution_journeys import BY_SLUG, JOURNEYS


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation", "ai"])
def test_each_experience_scenario_generates_a_downloadable_specification(sector):
    blueprint = make_blueprint(
        sector=sector,
        team="growth",
        process="legacy",
        priority="control",
        integrations=("database", "external"),
    )
    specification = compile_specification(
        sector=sector,
        team="growth",
        process="legacy",
        priority="control",
        integrations=("database", "external"),
    )
    assert blueprint.sector == sector
    assert blueprint.components
    assert blueprint.acceptance
    assert blueprint.risks
    assert blueprint.lead_url.startswith("/studio?topic=")
    assert specification.blueprint == blueprint
    assert specification.revision
    assert "Предварительное техническое задание" in specification.markdown


def test_experience_lab_and_blueprint_have_matching_sectors():
    assert {journey.slug for journey in JOURNEYS} == {option.key for option in SECTORS}
    assert set(BY_SLUG) == {option.key for option in SECTORS}
    for journey in JOURNEYS:
        assert journey.service_url.startswith("/services/")
        assert journey.case_url.startswith("/cases/")
        assert len(journey.steps) >= 4
        assert len({step.code for step in journey.steps}) == len(journey.steps)


def test_ai_scenario_is_explicitly_non_live_and_requires_human_review():
    journey = BY_SLUG["ai"]
    assert len(journey.steps) == 6
    assert "не обращается" in " ".join(journey.constraints)
    assert "человек" in " ".join(journey.constraints)
    brief = make_blueprint("ai", "solo", "manual", "experience")
    assert any("подтверждения" in item for item in brief.acceptance)
    assert any("качества" in item for item in brief.components)


@pytest.mark.parametrize("bad_sector", ["", "unknown", "../admin", "AI"])
def test_unknown_sectors_are_rejected(bad_sector):
    with pytest.raises(ValueError):
        make_blueprint(bad_sector, "solo", "new", "speed")


def test_specification_identity_is_stable_for_integration_order():
    first = compile_specification(
        sector="ai", team="growth", process="new", priority="control",
        integrations=("external", "database"),
    )
    second = compile_specification(
        sector="ai", team="growth", process="new", priority="control",
        integrations=("database", "external"),
    )
    assert first.revision == second.revision
    assert first.markdown == second.markdown
