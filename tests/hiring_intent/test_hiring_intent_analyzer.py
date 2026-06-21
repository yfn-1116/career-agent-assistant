"""Tests for hiring intent analyzer."""

from career_agent.hiring_intent.analyzer import HiringIntentAnalyzer, HiringIntentResult


GOOD_JD = """AI Agent 开发实习生
深圳 · 实习 · 本科 · 300-400/天

岗位职责：
1. 参与 AI Agent 应用开发和 RAG 检索系统优化
2. 使用 LangGraph 搭建多步骤 Agent workflow
3. 实现工具调用和检索评分模块

岗位要求：
- Python, LangChain, LangGraph, RAG
- 向量数据库 Chroma/FAISS
- LLM API 调用经验
- 实习 3-6 个月，每周 4-5 天
"""

VAGUE_JD = """AI 开发实习生
公司：XX科技
要求：熟悉人工智能相关技术，完成领导安排的任务
"""

KEYWORD_STUFFING_JD = """AI 实习生
要求：Python, Java, React, Vue, Docker, Kubernetes, TensorFlow, OpenCV, NLP, 销售, 运营, 短视频, 直播, Photoshop
"""

TITLE_MISMATCH_JD = """AI 工程师实习
职责：1. 课程推广 2. 社群运营 3. 客户转化 4. 直播带货
要求：有销售经验优先，沟通能力强
"""


class TestHiringIntentAnalyzer:
    def test_good_jd_high_intent(self):
        r = HiringIntentAnalyzer().analyze(jd_text=GOOD_JD, hard_skills=["Python", "LangGraph", "RAG", "Chroma"],
                                           job_title="AI Agent 开发实习生")
        assert r.hiring_intent_score >= 0.65
        assert r.intent_level in ("likely_active", "uncertain")
        assert len(r.positive_signals) > 0

    def test_vague_jd_low_intent(self):
        r = HiringIntentAnalyzer().analyze(jd_text=VAGUE_JD, hard_skills=["人工智能"],
                                           job_title="AI 开发实习生")
        assert r.hiring_intent_score < 0.6
        assert "vague_jd" in r.risk_flags

    def test_keyword_stuffing_flagged(self):
        skills = ["Python", "Java", "React", "Vue", "Docker", "Kubernetes", "TensorFlow", "OpenCV",
                  "NLP", "销售", "运营", "短视频", "直播", "Photoshop"]
        r = HiringIntentAnalyzer().analyze(jd_text=KEYWORD_STUFFING_JD, hard_skills=skills, job_title="AI 实习生")
        assert "keyword_stuffing" in r.risk_flags

    def test_title_content_mismatch(self):
        r = HiringIntentAnalyzer().analyze(jd_text=TITLE_MISMATCH_JD, hard_skills=["销售", "运营", "直播"],
                                           job_title="AI 工程师实习")
        assert "title_content_mismatch" in r.risk_flags
        assert r.risk_score > 0

    def test_hr_asks_project_improves_reply_probability(self):
        interaction = {"has_reply": True, "asked_project_question": True, "asked_for_resume": True}
        r = HiringIntentAnalyzer().analyze(jd_text=GOOD_JD, hard_skills=["Python"], interaction=interaction)
        assert r.reply_probability_score >= 0.5

    def test_payment_request_flagged_risky(self):
        interaction = {"asked_payment_or_training": True}
        r = HiringIntentAnalyzer().analyze(jd_text=GOOD_JD, hard_skills=["Python"], interaction=interaction)
        assert r.risk_score >= 0.1
        assert "asked_payment_or_training" in r.risk_flags
        assert r.recommended_action == "skip"

    def test_generates_verification_questions(self):
        r = HiringIntentAnalyzer().analyze(jd_text=VAGUE_JD, hard_skills=["Python"], job_title="AI 实习生")
        assert len(r.verification_questions) > 0

    def test_all_scores_valid(self):
        r = HiringIntentAnalyzer().analyze(jd_text=GOOD_JD, hard_skills=["Python"])
        assert 0.0 <= r.hiring_intent_score <= 1.0
        assert 0.0 <= r.reply_probability_score <= 1.0
        assert 0.0 <= r.risk_score <= 1.0

    def test_to_dict(self):
        r = HiringIntentAnalyzer().analyze(jd_text=GOOD_JD, hard_skills=["Python"], job_title="Agent Intern")
        d = r.to_dict()
        assert d["intent_level"] == r.intent_level
        assert d["hiring_intent_score"] == r.hiring_intent_score
