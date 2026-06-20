"""Job-match workflow — orchestrates the full agent pipeline."""

from datetime import datetime, timezone
from pathlib import Path

from career_agent.agents.build_agent import BuildAgent
from career_agent.agents.jd_parser import JDParserAgent
from career_agent.agents.match_analysis_agent import MatchAnalysisAgent
from career_agent.agents.rag_retrieve_agent import RAGRetrieveAgent
from career_agent.agents.state import AgentTaskState
from career_agent.rag.pipeline import RAGPipeline


class JobMatchWorkflow:
    """Orchestrate JD parsing → evidence retrieval → analysis → output.

    Usage::

        wf = JobMatchWorkflow(profile_dir="data/samples/profile")
        state = wf.run(job_description_text)
        print(state.generated_output.summary)
    """

    def __init__(
        self,
        profile_dir: str | Path | None = None,
        rag_pipeline: RAGPipeline | None = None,
        jd_parser: JDParserAgent | None = None,
        rag_retrieve_agent: RAGRetrieveAgent | None = None,
        match_analysis_agent: MatchAnalysisAgent | None = None,
        build_agent: BuildAgent | None = None,
    ) -> None:
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.jd_parser = jd_parser or JDParserAgent()
        self.rag_retrieve_agent = rag_retrieve_agent or RAGRetrieveAgent(
            pipeline=self.rag_pipeline
        )
        self.match_analysis_agent = (
            match_analysis_agent or MatchAnalysisAgent()
        )
        self.build_agent = build_agent or BuildAgent()

        if profile_dir is not None:
            self.rag_pipeline.build_index(profile_dir)

    def run(self, job_description: str, top_k: int = 5) -> AgentTaskState:
        """Execute the full pipeline and return the final state."""
        state = AgentTaskState(job_description=job_description)
        try:
            # Step 1 — parse JD
            state.parsed_jd = self.jd_parser.parse(job_description)

            # Step 2 — retrieve evidence
            state.retrieved_evidence = self.rag_retrieve_agent.retrieve(
                parsed_jd=state.parsed_jd, top_k=top_k
            )

            # Step 3 — match analysis
            state.match_analysis = self.match_analysis_agent.analyze(
                parsed_jd=state.parsed_jd,
                evidence=state.retrieved_evidence,
            )

            # Step 4 — build output
            state.generated_output = self.build_agent.build(
                parsed_jd=state.parsed_jd,
                evidence=state.retrieved_evidence,
                match_analysis=state.match_analysis,
            )

            state.status = "completed"
        except Exception as exc:
            state.status = "failed"
            state.error_message = str(exc)
        finally:
            state.updated_at = datetime.now(timezone.utc).isoformat()

        return state
