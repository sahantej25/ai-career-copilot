"""Professional LaTeX resume builder (reference template) + PyLaTeX PDF compile."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from models.schemas import CandidateProfile, ResumePreviewResponse, Skill, TailoredExperienceEntry
from services.guardrails.constants import MAX_EXPERIENCE_BULLETS, MAX_LATEX_SOURCE_CHARS
from services.pdf_service import DEFAULT_SECTION_ORDER, generate_resume_pdf

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "resume"
_PREAMBLE = (_TEMPLATE_DIR / "preamble.tex").read_text(encoding="utf-8")

_LATEX_FORBIDDEN = re.compile(
    r"\\(?:write18|immediate|openout|write|csname|newwrite|ShellEscape)\b",
    re.IGNORECASE,
)

_CATEGORY_LABELS = {
    "programming": "Programming",
    "framework": "Frameworks",
    "database": "Databases",
    "cloud": "Cloud",
    "tool": "Tools",
    "soft-skill": "Soft Skills",
    "domain": "Domain Expertise",
    "frontend": "Frontend",
    "backend": "Backend",
    "general": "Technical Skills",
    "other": "Technical Skills",
}


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters in plain text."""
    if not text:
        return ""
    replacements = (
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    )
    result = text
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def sanitize_latex_source(source: str) -> str:
    if not source or not source.strip():
        return ""
    cleaned = _LATEX_FORBIDDEN.sub("", source)
    return cleaned[:MAX_LATEX_SOURCE_CHARS]


def _format_name_header(name: str) -> str:
    display = escape_latex(name.strip() or "Candidate").upper()
    return rf"\textbf{{\Huge \scshape {display} }}"


def _format_contact_line(profile: CandidateProfile) -> str:
    parts: list[str] = []
    if profile.email:
        email = escape_latex(profile.email)
        parts.append(rf"\href{{mailto:{email}}}{{{email}}}")
    if profile.phone:
        parts.append(escape_latex(profile.phone))
    if profile.location:
        parts.append(escape_latex(profile.location))
    if not parts:
        return ""
    return " $|$ ".join(parts)


def _section(title: str) -> str:
    return rf"\section{{\color{{Blue}} {escape_latex(title)}}}"


def _group_skills(profile: CandidateProfile, ordered_names: list[str]) -> list[tuple[str, list[str]]]:
    """Group skills by category; preserve JD-prioritized order within each group."""
    by_name: dict[str, Skill] = {s.name.lower(): s for s in profile.skills}
    order_index = {n.lower(): i for i, n in enumerate(ordered_names)}

    buckets: dict[str, list[str]] = {}
    for skill_name in ordered_names:
        skill = by_name.get(skill_name.lower())
        cat = (skill.category if skill else "general") or "general"
        label = _CATEGORY_LABELS.get(cat.lower(), cat.replace("-", " ").title())
        buckets.setdefault(label, []).append(skill_name)

    for skill in profile.skills:
        if skill.name.lower() in order_index:
            continue
        label = _CATEGORY_LABELS.get(skill.category.lower(), skill.category.replace("-", " ").title())
        buckets.setdefault(label, []).append(skill.name)

    return sorted(buckets.items(), key=lambda x: min(order_index.get(n.lower(), 999) for n in x[1]))


def _skills_block(profile: CandidateProfile, ordered_skills: list[str]) -> str:
    groups = _group_skills(profile, ordered_skills)
    if not groups:
        return ""
    lines = [_section("Technical Skills"), r"\vspace{-2mm}"]
    for label, names in groups:
        skill_text = ", ".join(escape_latex(n) for n in names)
        lines.append(rf"• \textbf{{{escape_latex(label)}:}} {{{skill_text}}} \\")
    return "\n".join(lines) + "\n"


def _experience_block(
    profile: CandidateProfile,
    entries: list[TailoredExperienceEntry],
) -> str:
    if not entries:
        return ""
    location = escape_latex(profile.location) if profile.location else ""
    lines = [_section("Experience"), r"\vspace{-2mm}"]

    for exp in entries:
        role = escape_latex(exp.role)
        company = escape_latex(exp.company)
        duration = escape_latex(exp.duration)
        loc_part = f" $|$ {location}" if location else ""
        lines.append(rf"{{\bf {role}{loc_part} $|$ {company} }} \hfill {{\bf {duration}}}")
        lines.append("")
        lines.append(r"\begin{itemize}")
        lines.append(r"\justifying")
        for bullet in exp.bullets[:MAX_EXPERIENCE_BULLETS]:
            if bullet.strip():
                lines.append(f"    \\item {escape_latex(bullet.strip())}")
                lines.append("")
        lines.append(r"\end{itemize}")
        lines.append(r"\vspace{2mm}")

    return "\n".join(lines)


def _projects_block(
    profile: CandidateProfile,
    highlighted: list[str],
) -> str:
    if not profile.projects:
        return ""
    highlight_set = {p.lower() for p in highlighted}
    ordered = sorted(
        profile.projects,
        key=lambda p: 0 if p.name.lower() in highlight_set else 1,
    )
    lines = [_section("Projects"), r"\vspace{-2mm}"]
    for proj in ordered[:8]:
        tech = ", ".join(proj.technologies) if proj.technologies else ""
        title = escape_latex(proj.name)
        tech_part = rf" $|$ \textit{{Tech Stack: {escape_latex(tech)}}}" if tech else ""
        lines.append(rf"\textbf{{{title}}}{tech_part}")
        lines.append(r"\begin{itemize}")
        lines.append(r"\justifying")
        if proj.description:
            for chunk in proj.description.split("\n"):
                chunk = chunk.strip()
                if chunk:
                    lines.append(f"\\item {escape_latex(chunk)}")
        lines.append(r"\end{itemize}")
        lines.append(r"\vspace{2mm}")
    return "\n".join(lines)


def _education_block(profile: CandidateProfile) -> str:
    if not profile.education:
        return ""
    lines = [_section("Education "), r"\resumeSubHeadingListStart"]
    for edu in profile.education:
        institution = escape_latex(edu.institution)
        degree = escape_latex(edu.degree)
        year = escape_latex(edu.year)
        lines.append(r"    \resumeSubheading")
        lines.append(rf"      {{{institution}}}{{\hfill \bf {year}}}")
        lines.append(rf"      {{{degree}}}{{}}")
    lines.append(r"  \resumeSubHeadingListEnd")
    lines.append(r"\vspace{-2mm}")
    return "\n".join(lines)


def build_latex_document(
    profile: CandidateProfile,
    package: ResumePreviewResponse,
    *,
    accent_hex: str = "#10b981",  # noqa: ARG001 — kept for API compatibility
) -> str:
    """Build a complete LaTeX document matching the reference resume template."""
    order = [s for s in (package.section_order or DEFAULT_SECTION_ORDER) if s in DEFAULT_SECTION_ORDER]
    for sec in DEFAULT_SECTION_ORDER:
        if sec not in order:
            order.append(sec)

    entries = package.tailored_experience
    if not entries and profile.experience:
        entries = [
            TailoredExperienceEntry(
                company=exp.company,
                role=exp.role,
                duration=exp.duration,
                bullets=exp.description[:MAX_EXPERIENCE_BULLETS],
            )
            for exp in profile.experience
        ]

    summary = package.tailored_summary or profile.summary
    body_parts: list[str] = [
        r"\begin{document}",
        r"\begin{center}",
        f"    {_format_name_header(profile.name)} \\\\ \\vspace{{1pt}}",
    ]
    contact = _format_contact_line(profile)
    if contact:
        body_parts.append(f"    {contact}")
    body_parts.append(r"\end{center}")

    section_builders = {
        "summary": lambda: (
            _section("Professional Summary")
            + "\n\\setlist{nolistsep}\n\\justifying\n\\vspace{1mm}\n"
            + escape_latex(summary)
            + "\n\\vspace{-2mm}\n"
            if summary
            else ""
        ),
        "skills": lambda: _skills_block(profile, package.ordered_skills),
        "experience": lambda: _experience_block(profile, entries),
        "projects": lambda: _projects_block(profile, package.highlighted_projects or []),
        "education": lambda: _education_block(profile),
    }

    for sec in order:
        block = section_builders[sec]()
        if block:
            body_parts.append(block)

    body_parts.append(r"\end{document}")
    body = "\n".join(body_parts)
    return sanitize_latex_source(_PREAMBLE + "\n\n" + body)


def pylatex_compiler_available() -> bool:
    try:
        import pylatex  # noqa: F401
    except ImportError:
        return False
    return shutil.which("pdflatex") is not None


def compile_latex_to_pdf(latex_source: str, *, timeout: int = 60) -> bytes:
    """Compile LaTeX source to PDF using PyLaTeX's PDF generator + pdflatex."""
    from pylatex import Document

    if not pylatex_compiler_available():
        raise RuntimeError("PyLaTeX and pdflatex are required for PDF compilation.")

    safe_source = sanitize_latex_source(latex_source)
    if not safe_source.strip():
        raise RuntimeError("Empty LaTeX source.")

    source_holder = {"tex": safe_source}

    class _TemplateDocument(Document):
        """PyLaTeX document that compiles pre-rendered .tex source."""

        def generate_tex_file(self, filepath: str | None = None) -> None:
            path = filepath or self.filepath
            Path(path).write_text(source_holder["tex"], encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        base = work / "resume"
        doc = _TemplateDocument(
            documentclass="article",
            documentclass_options=["letterpaper", "10pt", "usenames", "dvipsnames"],
        )
        doc.filepath = str(base) + ".tex"
        doc.filename = str(base)

        try:
            doc.generate_pdf(str(base), compiler="pdflatex", clean_tex=False, silent=True)
        except subprocess.CalledProcessError as exc:
            log = work / "resume.log"
            detail = log.read_text(encoding="utf-8", errors="ignore")[-2000:] if log.exists() else str(exc)
            raise RuntimeError(f"PyLaTeX PDF compilation failed.\n{detail}") from exc

        pdf_path = Path(f"{base}.pdf")
        if not pdf_path.exists():
            raise RuntimeError("PyLaTeX did not produce a PDF file.")
        return pdf_path.read_bytes()


def generate_resume_pdf_from_package(
    profile: CandidateProfile,
    package: ResumePreviewResponse,
    *,
    accent_hex: str = "#10b981",
    latex_source: Optional[str] = None,
) -> tuple[bytes, str]:
    """Generate PDF from LaTeX via PyLaTeX; fall back to ReportLab if compile unavailable."""
    source = latex_source or package.latex_source or build_latex_document(
        profile, package, accent_hex=accent_hex,
    )
    source = sanitize_latex_source(source)

    if pylatex_compiler_available():
        try:
            return compile_latex_to_pdf(source), source
        except (RuntimeError, subprocess.TimeoutExpired, OSError):
            pass

    pdf_bytes = generate_resume_pdf(
        profile,
        package.tailored_summary,
        package.ordered_skills,
        highlighted_projects=package.highlighted_projects,
        tailored_experience=package.tailored_experience,
        section_order=package.section_order,
        accent_hex=accent_hex,
    )
    return pdf_bytes, source
