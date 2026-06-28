"""Normalize job listing text fields for safe display."""
from models.schemas import JobListing
from services.job_match_scorer import job_excerpt, strip_html


def sanitize_job_listing(job: JobListing) -> JobListing:
    plain_description = strip_html(job.description)
    plain_excerpt = strip_html(job.excerpt)
    source_text = plain_description or plain_excerpt
    return job.model_copy(
        update={
            "description": plain_description,
            "excerpt": job_excerpt(source_text) if source_text else "",
        }
    )
