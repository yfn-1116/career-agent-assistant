"""Hiring Intent Analyzer — estimates if a job posting is a real hiring need."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from career_agent.domain.validation import validate_score


@dataclass
class HiringIntentResult:
    hiring_intent_score: float = 0.5
    reply_probability_score: float = 0.5
    risk_score: float = 0.0
    intent_level: str = "uncertain"
    positive_signals: list[str] = field(default_factory=list)
    negative_signals: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    verification_questions: list[str] = field(default_factory=list)
    recommended_action: str = "skip"
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        import dataclasses
        return {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}


class HiringIntentAnalyzer:
    """Analyze job posting quality and hiring intent from text signals."""

    def analyze(self, jd_text: str = "", hard_skills: list[str] | None = None,
                job_title: str = "", company: str = "", platform: str = "",
                interaction: dict[str, Any] | None = None) -> HiringIntentResult:
        skills = hard_skills or []
        text = jd_text.strip()
        positive, negative, risks = [], [], []

        # 1. JD specificity
        jd_spec = self._jd_specificity(text, skills, positive, negative, risks)

        # 2. Skill coherence
        skill_coh = self._skill_coherence(skills, job_title, positive, negative, risks)

        # 3. Role-business alignment (neutral if no company info)
        role_align = 0.5

        # 4. Freshness (neutral if no timestamp)
        freshness = 0.5

        # 5. Compensation reasonableness
        comp_reason = 0.5

        # 6. Interaction quality
        interaction_q = self._interaction_quality(interaction, positive, negative, risks)

        # Weighted score
        hiring_intent = round(
            0.30 * jd_spec + 0.20 * skill_coh + 0.15 * role_align
            + 0.15 * freshness + 0.10 * comp_reason + 0.10 * interaction_q, 4,
        )

        # Risk score
        risk_score = round(min(1.0, len(risks) * 0.15), 4)
        reply_prob = round(hiring_intent * 0.9, 4)

        # Intent level
        if risk_score >= 0.70:
            intent_level = "risky"
        elif hiring_intent >= 0.70:
            intent_level = "likely_active"
        elif hiring_intent >= 0.45:
            intent_level = "uncertain"
        else:
            intent_level = "low_intent"

        # Recommended action
        if risk_score >= 0.70:
            action = "skip"
        elif hiring_intent >= 0.70:
            action = "prioritize_contact"
        elif hiring_intent >= 0.45:
            action = "contact_with_verification"
        else:
            action = "low_priority"

        explanation = f"JD具体度={jd_spec:.2f}, 技能一致性={skill_coh:.2f}, 交互质量={interaction_q:.2f}"
        if risks:
            explanation += f", 风险信号={len(risks)}个"

        # Generate verification questions
        questions = self._generate_questions(job_title, skills, risks)

        return HiringIntentResult(
            hiring_intent_score=validate_score(hiring_intent, "hiring_intent_score"),
            reply_probability_score=validate_score(reply_prob, "reply_probability_score"),
            risk_score=validate_score(risk_score, "risk_score"),
            intent_level=intent_level,
            positive_signals=positive,
            negative_signals=negative,
            risk_flags=risks,
            verification_questions=questions,
            recommended_action=action,
            explanation=explanation,
        )

    @staticmethod
    def _jd_specificity(text: str, skills: list[str], pos: list, neg: list, risks: list) -> float:
        score = 0.5
        if len(text) >= 200:
            score += 0.2; pos.append("JD 内容较详细")
        elif len(text) < 80:
            score -= 0.3; neg.append("JD 过短"); risks.append("vague_jd")
        if skills and len(skills) >= 3:
            score += 0.15; pos.append(f"明确技能要求 ({len(skills)} 项)")
        if skills and len(skills) > 12:
            score -= 0.2; neg.append("技能过多可能乱堆"); risks.append("keyword_stuffing")
        if any(kw in text for kw in ["职责", "工作内容", "任务", "岗位要求"]):
            score += 0.1; pos.append("有明确职责描述")
        else:
            score -= 0.1; neg.append("缺少职责描述")
        if any(kw in text for kw in ["到岗", "实习周期", "天数", "薪资"]):
            score += 0.05; pos.append("有实习具体信息")
        return max(0.0, min(1.0, score))

    @staticmethod
    def _skill_coherence(skills: list[str], job_title: str, pos: list, neg: list, risks: list) -> float:
        if not skills or not job_title:
            return 0.5
        title_lower = job_title.lower()
        # Check if title and skills align
        agent_skills = {"langgraph", "langchain", "rag", "agent", "tool calling", "llm", "prompt"}
        cv_skills = {"opencv", "pytorch", "cnn", "tensorflow", "yolo", "图像"}
        backend_skills = {"fastapi", "django", "flask", "spring", "api", "restful", "postgresql"}
        sales_skills = {"销售", "运营", "直播", "课程", "引流", "社群"}

        skill_set = {s.lower() for s in skills}
        is_agent = any(s in skill_set for s in agent_skills)
        is_cv = any(s in skill_set for s in cv_skills)
        is_backend = any(s in skill_set for s in backend_skills)
        is_sales = any(s in skill_set for s in sales_skills)

        # Mismatch detection
        if ("agent" in title_lower or "ai" in title_lower or "rag" in title_lower) and is_sales:
            risks.append("title_content_mismatch"); neg.append("标题和内容不一致(AI岗写销售内容)"); return 0.1
        if is_agent and is_cv and is_backend and is_sales:
            risks.append("keyword_stuffing"); neg.append("技能跨多个不相关领域"); return 0.2
        if len(skill_set) > 10:
            risks.append("keyword_stuffing"); neg.append("技能过多且跨域"); return 0.25
        if is_agent or is_cv or is_backend:
            pos.append(f"技能与岗位方向一致"); return 0.85
        return 0.5

    @staticmethod
    def _interaction_quality(interaction: dict[str, Any] | None, pos: list, neg: list, risks: list) -> float:
        if not interaction:
            return 0.5
        score = 0.5
        if interaction.get("asked_for_resume"):
            score += 0.15; pos.append("HR 要求简历（正向信号）")
        if interaction.get("asked_project_question"):
            score += 0.15; pos.append("HR 询问具体项目")
        if interaction.get("gave_specific_job_details"):
            score += 0.1; pos.append("HR 提供岗位细节")
        if interaction.get("suspicious_redirect"):
            score -= 0.4; neg.append("HR 诱导跳转"); risks.append("suspicious_redirect")
        if interaction.get("asked_payment_or_training"):
            score -= 0.5; neg.append("涉及付费或培训"); risks.append("asked_payment_or_training"); risks.append("asked_payment_or_training"); risks.append("asked_payment_or_training"); risks.append("asked_payment_or_training"); risks.append("asked_payment_or_training")
        if interaction.get("has_reply"):
            score += 0.1
        return max(0.0, min(1.0, score))

    @staticmethod
    def _generate_questions(job_title: str, skills: list[str], risks: list) -> list[str]:
        qs = ["请问这个岗位目前还在招吗？"]
        if "vague_jd" in risks:
            qs.append("实习生主要参与哪一块任务或项目？")
        if "keyword_stuffing" in risks:
            qs.append("这个岗位更偏向哪方面技术，主要用什么技术栈？")
        if "title_content_mismatch" in risks:
            qs.append("想确认一下，这个岗位的实际工作内容主要是什么？")
        if skills:
            top = skills[:3]
            qs.append(f"实习任务是否主要围绕 {', '.join(top)} 展开？")
        qs.append("实习周期和每周到岗天数有什么要求？")
        return qs[:4]
