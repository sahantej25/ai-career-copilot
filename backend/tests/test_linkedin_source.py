import pytest

from services.sources.linkedin_source import _parse_linkedin_html, _clean_title


SAMPLE_HTML = """
<li>
  <div data-entity-urn="urn:li:jobPosting:12345">
    <a href="https://www.linkedin.com/jobs/view/software-engineer-at-acme-12345?position=1">link</a>
    <span class="sr-only">Software Engineer</span>
    <a class="hidden-nested-link">Acme Corp</a>
    <span class="job-search-card__location">San Francisco, CA</span>
    <time datetime="2026-06-26T08:00:00">1 day ago</time>
  </div>
</li>
"""


def test_parse_linkedin_html():
    rows = _parse_linkedin_html(SAMPLE_HTML)
    assert len(rows) == 1
    assert rows[0]["id"] == "12345"
    assert rows[0]["title"] == "Software Engineer"
    assert rows[0]["company"] == "Acme Corp"
    assert "linkedin.com/jobs/view" in rows[0]["url"]
    assert rows[0]["published_at"] == "2026-06-26T08:00:00Z"


def test_clean_title():
    assert _clean_title("  Hello   World  ") == "Hello World"
