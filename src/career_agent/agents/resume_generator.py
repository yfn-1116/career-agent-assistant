"""Resume generator — produces a complete resume from match results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from career_agent.agents.state import GeneratedOutput, MatchAnalysisResult, ParsedJD


@dataclass
class ResumeTemplate:
    """A resume template with sections."""

    name: str = "default"
    sections: list[str] = field(default_factory=lambda: [
        "personal_info", "education", "skills", "projects", "internship", "self_eval",
    ])
    style: str = "markdown"


# Built-in templates
TEMPLATES = {
    "default": ResumeTemplate(name="default"),
    "minimal": ResumeTemplate(
        name="minimal",
        sections=["personal_info", "skills", "projects"],
    ),
    "full": ResumeTemplate(
        name="full",
        sections=["personal_info", "education", "skills", "projects", "internship", "certificates", "self_eval"],
    ),
}


class ResumeGenerator:
    """Generate a complete Markdown resume from parsed JD, evidence, and analysis.

    Usage::

        gen = ResumeGenerator(template="default")
        resume_md = gen.generate(parsed_jd, generated_output, match_analysis,
                                 profile_info={"name": "张三", "school": "XX大学"})
    """

    def __init__(self, template: str = "default") -> None:
        self.template = TEMPLATES.get(template, TEMPLATES["default"])

    def generate(
        self,
        parsed_jd: ParsedJD | None = None,
        generated_output: GeneratedOutput | None = None,
        match_analysis: MatchAnalysisResult | None = None,
        profile_info: dict[str, Any] | None = None,
    ) -> str:
        """Generate a complete resume as Markdown."""
        info = profile_info or {}
        lines: list[str] = []
        L = lines.append

        L(f"# {info.get('name', '姓名')}")
        L("")

        for section in self.template.sections:
            content = self._render_section(section, parsed_jd, generated_output, match_analysis, info)
            if content:
                L(content)
                L("")

        return "\n".join(lines)

    def _render_section(
        self,
        section: str,
        parsed_jd: ParsedJD | None,
        generated_output: GeneratedOutput | None,
        match_analysis: MatchAnalysisResult | None,
        info: dict[str, Any],
    ) -> str:
        if section == "personal_info":
            return self._personal_info(info)
        elif section == "education":
            return self._education(info)
        elif section == "skills":
            return self._skills(parsed_jd, match_analysis)
        elif section == "projects":
            return self._projects(generated_output)
        elif section == "internship":
            return self._internship(info)
        elif section == "self_eval":
            return self._self_eval(match_analysis)
        elif section == "certificates":
            return self._certificates(info)
        return ""

    @staticmethod
    def _personal_info(info: dict[str, Any]) -> str:
        parts = ["## 个人信息", ""]
        for key, label in [("name", "姓名"), ("school", "学校"), ("major", "专业"),
                           ("degree", "学历"), ("email", "邮箱"), ("phone", "电话"),
                           ("github", "GitHub"), ("city", "期望城市")]:
            if info.get(key):
                parts.append(f"- **{label}**：{info[key]}")
        return "\n".join(parts)

    @staticmethod
    def _education(info: dict[str, Any]) -> str:
        if not info.get("school"):
            return ""
        lines = ["## 教育经历", ""]
        lines.append(f"- {info.get('school', '')} | {info.get('major', '')} | {info.get('degree', '')}")
        if info.get("education_extra"):
            lines.append(f"  {info['education_extra']}")
        return "\n".join(lines)

    @staticmethod
    def _skills(parsed_jd: ParsedJD | None, match_analysis: MatchAnalysisResult | None) -> str:
        lines = ["## 技能", ""]
        if parsed_jd and parsed_jd.hard_skills:
            lines.append(f"- **岗位相关**：{', '.join(parsed_jd.hard_skills[:10])}")
        if match_analysis and match_analysis.matched_keywords:
            lines.append(f"- **匹配技能**：{', '.join(match_analysis.matched_keywords[:10])}")
        return "\n".join(lines) if len(lines) > 2 else ""

    @staticmethod
    def _projects(generated_output: GeneratedOutput | None) -> str:
        if not generated_output or not generated_output.resume_bullets:
            return ""
        lines = ["## 项目经历", ""]
        for i, bullet in enumerate(generated_output.resume_bullets[:5], 1):
            # Clean up the bullet text
            text = bullet.replace("# ", "").replace("\n", " ")[:200]
            lines.append(f"{i}. {text}")
        return "\n".join(lines)

    @staticmethod
    def _internship(info: dict[str, Any]) -> str:
        if not info.get("internship"):
            return ""
        lines = ["## 实习经历", ""]
        lines.append(info["internship"])
        return "\n".join(lines)

    @staticmethod
    def _self_eval(match_analysis: MatchAnalysisResult | None) -> str:
        lines = ["## 自我评价", ""]
        if match_analysis and match_analysis.strengths:
            lines.append(f"擅长：{'、'.join(match_analysis.strengths[:5])}")
        if match_analysis and match_analysis.suggestions:
            lines.append(f"发展方向：{'、'.join(match_analysis.suggestions[:3])}")
        return "\n".join(lines) if len(lines) > 2 else ""

    @staticmethod
    def _certificates(info: dict[str, Any]) -> str:
        if not info.get("certificates"):
            return ""
        return f"## 证书\n\n{info['certificates']}"
