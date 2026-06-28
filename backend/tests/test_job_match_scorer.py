from models.schemas import CandidateProfile, JobListing, Skill
from services.job_match_scorer import score_job_for_profile, strip_html


def test_strip_html():
    assert strip_html("<p>Hello <b>World</b></p>") == "Hello World"
    assert strip_html("&lt;strong&gt;Hi&lt;/strong&gt;") == "Hi"


def test_score_job_with_matching_profile():
    job = JobListing(
        id="remotive:1",
        title="Senior React Engineer",
        company="Acme",
        description="We need React, TypeScript, and Node.js experience.",
        tags=["React", "TypeScript", "Node.js"],
        apply_url="https://example.com/apply",
        source="remotive",
    )
    profile = CandidateProfile(
        name="Dev",
        skills=[
            Skill(name="React", confidence=90, category="frontend"),
            Skill(name="TypeScript", confidence=85, category="frontend"),
        ],
    )
    scored = score_job_for_profile(job, profile)
    assert scored.match_percentage is not None
    assert scored.match_percentage > 40
    assert "React" in scored.matched_skills


def test_score_job_without_profile():
    job = JobListing(
        id="remotive:2",
        title="Data Engineer",
        company="Globex",
        description="Python and SQL required.",
        apply_url="https://example.com/apply",
        source="remotive",
    )
    scored = score_job_for_profile(job, None)
    assert scored.match_percentage is None
