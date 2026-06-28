"""Tests for location platform agent."""
import pytest

from agents.location_platform_agent import apply_location_platforms, resolve_platforms_for_location
from models.schemas import JobPreferences


@pytest.mark.asyncio
async def test_resolve_platforms_india():
    sources, rationale, researched = await resolve_platforms_for_location("India", use_ai=False)
    assert sources == ["linkedin", "naukri", "indeed_india"]
    assert "Naukri" in researched[0]
    assert rationale


@pytest.mark.asyncio
async def test_apply_location_platforms_updates_sources():
    prefs = JobPreferences(location="India", preferred_sources=["linkedin", "greenhouse", "hiringcafe"])
    updated = await apply_location_platforms(prefs)
    assert updated.preferred_sources == ["linkedin", "naukri", "indeed_india"]
