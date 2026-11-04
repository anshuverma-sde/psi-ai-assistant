import uuid
from typing import TYPE_CHECKING

from langgraph.graph import END, START, StateGraph

from app.modules.knowledge_base.retrieval.service import RetrievalService
from app.modules.reasoning.generation.answer_generator import AnswerGenerator
from app.modules.reasoning.graph.nodes import AskNodes
from app.modules.reasoning.graph.state import AskState
from app.modules.reasoning.understanding.decomposer import QuestionDecomposer

if TYPE_CHECKING:
    from app.container import Container


class AskGraph:
    """Compiled LangGraph workflow for one visitor question."""

    def __init__(self, nodes: AskNodes) -> None:
        g = StateGraph(AskState)
        g.add_node("classify", nodes.classify)
        g.add_node("retrieve", nodes.retrieve)
        g.add_node("gate", nodes.gate)
        g.add_node("decompose", nodes.decompose)
        g.add_node("evaluate", nodes.evaluate)
        g.add_node("combine", nodes.combine)
        g.add_node("generate", nodes.generate)
        g.add_node("no_answer", nodes.no_answer)

        g.add_edge(START, "classify")
        g.add_edge("classify", "retrieve")
        g.add_edge("retrieve", "gate")
        g.add_conditional_edges("gate", nodes.route_after_gate, ["no_answer", "decompose", "generate"])
        g.add_conditional_edges("decompose", nodes.route_after_decompose, ["evaluate", "generate"])
        g.add_edge("evaluate", "combine")
        g.add_edge("combine", "generate")
        g.add_edge("generate", END)
        g.add_edge("no_answer", END)
        self.graph = g.compile()

    async def run(self, *, org_id: uuid.UUID, org_name: str, question: str) -> AskState:
        return await self.graph.ainvoke(
            {"org_id": org_id, "org_name": org_name, "question": question,
             "decision_results": [], "decision_errors": [], "notices": [], "timings": {}}
        )

    def mermaid(self) -> str:
        return self.graph.get_graph().draw_mermaid()


def build_ask_graph(c: "Container") -> AskGraph:
    s = c.settings
    nodes = AskNodes(
        classifier=c.classifier,
        retrieval=RetrievalService(c.vector_store, c.embeddings, s.retrieval_top_k),
        decomposer=QuestionDecomposer(c.llm),
        generator=AnswerGenerator(c.llm),
        gate_strong=s.gate_strong_similarity,
        gate_min=s.gate_min_similarity,
        top_k=s.retrieval_top_k,
    )
    return AskGraph(nodes)
