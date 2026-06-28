"""Build rich, structured candidate context for matching and resume agents."""
from models.schemas import CandidateProfile


def build_profile_context(profile: CandidateProfile, *, include_confidence: bool = True) -> str:
    """Format profile with experience bullets and project detail for semantic matching."""
    lines = [
        f"Name: {profile.name}",
        f"Location: {profile.location}",
        f"Summary: {profile.summary}",
        f"Domains: {', '.join(profile.domains) or 'general'}",
    ]

    if profile.skills:
        lines.append("Skills:")
        for skill in profile.skills:
            if include_confidence:
                lines.append(f"  - {skill.name} ({skill.category}, {skill.confidence:.0f}% confidence)")
            else:
                lines.append(f"  - {skill.name} ({skill.category})")

    if profile.experience:
        lines.append("Work experience:")
        for exp in profile.experience:
            lines.append(f"  • {exp.role} at {exp.company} ({exp.duration})")
            for bullet in exp.description[:6]:
                if bullet.strip():
                    lines.append(f"      - {bullet.strip()}")

    if profile.projects:
        lines.append("Projects:")
        for proj in profile.projects:
            tech = ", ".join(proj.technologies[:8]) if proj.technologies else ""
            lines.append(f"  • {proj.name}" + (f" [{tech}]" if tech else ""))
            if proj.description.strip():
                lines.append(f"      - {proj.description.strip()[:400]}")

    if profile.education:
        lines.append("Education:")
        for edu in profile.education:
            lines.append(f"  • {edu.degree}, {edu.institution} ({edu.year})")

    return "\n".join(lines)
