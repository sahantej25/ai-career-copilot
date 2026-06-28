from models.schemas import JobListing
from services.job_match_scorer import job_excerpt, strip_html
from services.location_filter import job_matches_location


def test_strip_html_encoded_tags():
    assert strip_html("&lt;p&gt;Hello&lt;/p&gt;") == "Hello"


def test_strip_html_with_attributes():
    raw = '<p data-pm-slice="1 1 []"><strong>REQ ID: CSQ427R198</strong></p>'
    assert "REQ ID" in strip_html(raw)
    assert "<p" not in strip_html(raw)


def test_job_excerpt_word_boundary():
    text = "<p>" + "word " * 80 + "</p>"
    excerpt = job_excerpt(text, max_len=50)
    assert excerpt.endswith("…")
    assert "<" not in excerpt


def test_us_filter_excludes_netherlands():
    job = JobListing(
        id="greenhouse:databricks:1",
        title="Sr. Manager, AI Forward Deployed Engineering (FDE) – EMEA",
        company="Databricks",
        location="Amsterdam, Netherlands",
        description="Mission based role in EMEA",
        apply_url="https://example.com/apply",
        source="greenhouse",
    )
    assert job_matches_location(job, "United States") is False


def test_us_filter_includes_san_francisco():
    job = JobListing(
        id="greenhouse:stripe:1",
        title="Software Engineer",
        company="Stripe",
        location="San Francisco, CA",
        apply_url="https://example.com/apply",
        source="greenhouse",
    )
    assert job_matches_location(job, "United States") is True


def test_us_filter_includes_remote_us():
    job = JobListing(
        id="greenhouse:acme:1",
        title="Backend Engineer",
        company="Acme",
        location="Remote - United States",
        remote=True,
        apply_url="https://example.com/apply",
        source="greenhouse",
    )
    assert job_matches_location(job, "United States") is True
