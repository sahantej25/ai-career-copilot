"""LaTeX resume builder and PDF compiler (Python subprocess)."""
import io
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from models.schemas import CandidateProfile, ResumePreviewResponse, TailoredExperienceEntry
from services.guardrails.constants import MAX_EXPERIENCE_BULLETS, MAX_LATEX_SOURCE_CHARS
from services.pdf_service import DEFAULT_SECTION_ORDER, generate_resume_pdf

_LATEX_FORBIDDEN = re.compile(
    r"\\(?:input|include|write18|immediate|openout|write|csname|newwrite|ShellEscape)\b",
    re.IGNORECASE,
)


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
    """Strip dangerous LaTeX commands before compile."""
    if not source or not source.strip():
        return ""
    cleaned = _LATEX_FORBIDDEN.sub("", source)
    return cleaned[:MAX_LATEX_SOURCE_CHARS]


def _section_header(title: str, accent_hex: str) -> str:
    color = accent_hex.lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    return (
        f"\\vspace{{6pt}}\\noindent{{\\color[HTML]{{{color}}}\\textbf{{\\large {escape_latex(title)}}}}}"
        f"\\par\\vspace{{2pt}}\\hrule height 0.6pt\\vspace{{4pt}}\n"
    )


def _bullets(items: list[str]) -> str:
    if not items:
        return ""
    lines = ["\\begin{itemize}[leftmargin=*, nosep, topsep=2pt]"]
    for item in items[:MAX_EXPERIENCE_BULLETS]:
        if item.strip():
            lines.append(f"  \\item {escape_latex(item.strip())}")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def build_latex_document(
    profile: CandidateProfile,
    package: ResumePreviewResponse,
    *,
    accent_hex: str = "#10b981",
) -> str:
    """Build a complete LaTeX document from the tailored resume package."""
    order = [s for s in (package.section_order or DEFAULT_SECTION_ORDER) if s in DEFAULT_SECTION_ORDER]
    for sec in DEFAULT_SECTION_ORDER:
        if sec not in order:
            order.append(sec)

    highlighted = {p.lower() for p in (package.highlighted_projects or [])}
    contact = " \\ $|$ \\ ".join(
        escape_latex(x) for x in [profile.email, profile.phone, profile.location] if x
    )

    parts = [
        r"\documentclass[11pt,letterpaper]{article}",
        r"\usepackage[margin=0.75in]{geometry}",
        r"\usepackage{enumitem}",
        r"\usepackage{xcolor}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{microtype}",
        r"\pagestyle{empty}",
        r"\setlength{\parindent}{0pt}",
        r"\begin{document}",
        f"{{\\LARGE \\textbf{{{escape_latex(profile.name or 'Candidate')}}}}}\\\\[2pt]",
    ]
    if contact:
        parts.append(f"{{\\small {contact}}}\\\\[6pt]")

    def summary_block() -> str:
        if not package.tailored_summary:
            return ""
        return (
            _section_header("Professional Summary", accent_hex)
            + escape_latex(package.tailored_summary)
            + "\n"
        )

    def skills_block() -> str:
        if not package.ordered_skills:
            return ""
        chunks = [package.ordered_skills[i : i + 5] for i in range(0, len(package.ordered_skills), 5)]
        body = " \\\\ ".join(", ".join(escape_latex(s) for s in chunk) for chunk in chunks)
        return _section_header("Skills", accent_hex) + body + "\n"

    def experience_block() -> str:
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
        if not entries:
            return ""
        lines = [_section_header("Experience", accent_hex)]
        for exp in entries:
            lines.append(
                f"\\textbf{{{escape_latex(exp.role)}}} \\hfill {escape_latex(exp.duration)}\\\\"
            )
            lines.append(
                f"\\textit{{{escape_latex(exp.company)}}}\\\\[2pt]"
            )
            lines.append(_bullets(exp.bullets))
            lines.append("\\vspace{4pt}")
        return "\n".join(lines)

    def projects_block() -> str:
        if not profile.projects:
            return ""
        ordered = sorted(profile.projects, key=lambda p: 0 if p.name.lower() in highlighted else 1)
        lines = [_section_header("Projects", accent_hex)]
        for proj in ordered[:8]:
            tech = ", ".join(proj.technologies) if proj.technologies else ""
            title = escape_latex(proj.name)
            if tech:
                title += f" \\textit{{[{escape_latex(tech)}]}}"
            lines.append(f"\\textbf{{{title}}}\\\\")
            if proj.description:
                lines.append(f"{escape_latex(proj.description)}\\\\[4pt]")
        return "\n".join(lines)

    def education_block() -> str:
        if not profile.education:
            return ""
        lines = [_section_header("Education", accent_hex)]
        for edu in profile.education:
            lines.append(
                f"\\textbf{{{escape_latex(edu.degree)}}} \\hfill {escape_latex(edu.year)}\\\\"
            )
            lines.append(f"\\textit{{{escape_latex(edu.institution)}}}\\\\[4pt]")
        return "\n".join(lines)

    renderers = {
        "summary": summary_block,
        "skills": skills_block,
        "experience": experience_block,
        "projects": projects_block,
        "education": education_block,
    }
    for sec in order:
        block = renderers[sec]()
        if block:
            parts.append(block)

    parts.append(r"\end{document}")
    return sanitize_latex_source("\n".join(parts))


def latex_compiler_available() -> bool:
    return shutil.which("pdflatex") is not None


def compile_latex_to_pdf(latex_source: str, *, timeout: int = 45) -> bytes:
    """Compile LaTeX source to PDF via pdflatex. Raises RuntimeError on failure."""
    if not latex_compiler_available():
        raise RuntimeError("pdflatex is not installed on this system.")

    safe_source = sanitize_latex_source(latex_source)
    if not safe_source.strip():
        raise RuntimeError("Empty LaTeX source.")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        tex_path = work / "resume.tex"
        tex_path.write_text(safe_source, encoding="utf-8")
        for _ in range(2):
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "resume.tex"],
                cwd=work,
                capture_output=True,
                timeout=timeout,
            )
            if result.returncode != 0 and not (work / "resume.pdf").exists():
                log = (work / "resume.log")
                detail = log.read_text(encoding="utf-8", errors="ignore")[-1500:] if log.exists() else ""
                raise RuntimeError(f"LaTeX compilation failed.\n{detail}")

        pdf_path = work / "resume.pdf"
        if not pdf_path.exists():
            raise RuntimeError("LaTeX did not produce a PDF file.")
        return pdf_path.read_bytes()


def generate_resume_pdf_from_package(
    profile: CandidateProfile,
    package: ResumePreviewResponse,
    *,
    accent_hex: str = "#10b981",
    latex_source: Optional[str] = None,
) -> tuple[bytes, str]:
    """Generate PDF from LaTeX; fall back to ReportLab if compile unavailable."""
    source = latex_source or package.latex_source or build_latex_document(
        profile, package, accent_hex=accent_hex,
    )
    source = sanitize_latex_source(source)

    if latex_compiler_available():
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
