"""Tests for original-resume section extraction."""
from services.resume_latex_parser import (
    extract_certifications_text,
    extract_linkedin_url,
    extract_publications_items,
    extract_scholar_url,
)

_SAMPLE = """
PAVAN KUMAR
pavan@example.com
https://www.linkedin.com/in/pavan-kumar-m-4779071a3/
https://scholar.google.com/citations?user=abc

PROFESSIONAL SUMMARY
Engineer with ML experience.

PUBLICATIONS
1. First paper on AI systems published at ACM 2024.
2. Second paper at Interspeech 2025.

TECHNICAL SKILLS
Python, PyTorch

EXPERIENCE
Citigroup

CERTIFICATIONS
AWS Certified Generative AI Developer - Professional
https://www.credly.com/badges/example/public_url
"""


def test_extract_publications_items():
    items = extract_publications_items(_SAMPLE)
    assert len(items) == 2
    assert "ACM 2024" in items[0]


def test_extract_certifications_text():
    text = extract_certifications_text(_SAMPLE)
    assert "AWS Certified" in text


def test_extract_profile_links():
    assert "linkedin.com" in extract_linkedin_url(_SAMPLE)
    assert "scholar.google.com" in extract_scholar_url(_SAMPLE)
