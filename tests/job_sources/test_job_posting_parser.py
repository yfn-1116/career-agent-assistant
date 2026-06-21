from career_agent.job_sources.parser import JobPostingParser
from career_agent.job_sources.schema import JobPosting


BOSS_SAMPLE = """
AI Agent 开发实习生
深圳 · 实习 · 本科
300-400/天

公司：XX 科技有限公司

岗位要求：
- Python, LangChain, LangGraph, RAG
- 向量数据库 Chroma/FAISS
- LLM API 调用
- Git 协作

加分：
- Agent 系统项目经验
- Prompt Engineering
"""


class TestJobPostingParser:
    def test_parse_single(self):
        parser = JobPostingParser()
        posting = parser.parse(BOSS_SAMPLE, platform="boss")
        assert posting.job_title or posting.company
        assert posting.source_type == "manual"
        assert posting.hard_skills  # should find Python, RAG, etc
        assert "Python" in posting.hard_skills

    def test_parse_batch(self):
        text = BOSS_SAMPLE + "\n\n---\n\n" + BOSS_SAMPLE.replace("Agent", "Backend")
        parser = JobPostingParser()
        postings = parser.parse_batch(text)
        assert len(postings) >= 1

    def test_raw_text_preserved(self):
        parser = JobPostingParser()
        posting = parser.parse("test job text")
        assert posting.raw_text == "test job text"

    def test_to_dict(self):
        posting = JobPosting(job_title="Agent Intern", company="XX Tech")
        d = posting.to_dict()
        assert d["job_title"] == "Agent Intern"


class TestDiscoveryRanker:
    def test_rank_jobs(self):
        from career_agent.discovery.ranker import JobRanker
        from career_agent.profile.schema import STATUS_IMPLEMENTED, ProfileItem
        postings = [
            JobPosting(job_title="Agent Intern", hard_skills=["Python", "RAG", "LangGraph"]),
            JobPosting(job_title="K8s Engineer", hard_skills=["Kubernetes", "Docker"]),
        ]
        items = [ProfileItem(source_path="x", skills=["Python", "RAG", "LangGraph"], status=STATUS_IMPLEMENTED)]
        ranked = JobRanker().rank(postings, items)
        assert ranked[0].job_posting.job_title == "Agent Intern"
        assert ranked[0].match_score > ranked[1].match_score


class TestMessageAgent:
    def test_boss_greeting(self):
        from career_agent.messages.agent import MessageAgent
        agent = MessageAgent()
        draft = agent.generate("boss_greeting", job_title="AI Agent 实习", matched_skills=["Python", "RAG"])
        assert len(draft.text) > 20
        assert "Agent" in draft.text or "Python" in draft.text

    def test_hr_reply_project(self):
        from career_agent.messages.agent import MessageAgent
        agent = MessageAgent()
        draft = agent.generate("hr_reply", hr_question="你有项目经验吗", strengths=["Agent 项目"])
        assert "项目" in draft.text

    def test_no_skills_warns(self):
        from career_agent.messages.agent import MessageAgent
        agent = MessageAgent()
        draft = agent.generate("boss_greeting")
        assert draft.risk_warnings


class TestHRReplyAssistant:
    def test_classify_project(self):
        from career_agent.conversation.reply import HRReplyAssistant
        r = HRReplyAssistant().suggest("你有相关项目吗", {"strengths": ["RAG Agent"]})
        assert r.original_message
        assert r.suggested_reply

    def test_rejection_reply(self):
        from career_agent.conversation.reply import HRReplyAssistant
        r = HRReplyAssistant().suggest("不好意思不太合适")
        assert "感谢" in r.suggested_reply


class TestApprovalGate:
    def test_send_requires_approval(self):
        from career_agent.approval.gate import ApprovalGate
        req = ApprovalGate().check("send_greeting", preview_text="hello", target="XX公司")
        assert req.required
        assert req.status == "pending"

    def test_approve(self):
        from career_agent.approval.gate import ApprovalGate
        gate = ApprovalGate()
        req = gate.check("send_greeting", "hello")
        req = gate.approve(req)
        assert req.status == "approved"

    def test_not_send_no_approval_needed(self):
        from career_agent.approval.gate import ApprovalGate
        req = ApprovalGate().check("analyze_job")
        assert not req.required
