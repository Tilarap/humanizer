from langchain_core.messages import AIMessage

from app.agent import Evaluation, build_humanizer_graph


class FakeWriter:
    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)

    async def ainvoke(self, _messages: object) -> AIMessage:
        return AIMessage(content=next(self.responses))


class FakeEvaluator:
    def __init__(self, responses: list[Evaluation]) -> None:
        self.responses = iter(responses)

    async def ainvoke(self, _messages: object) -> Evaluation:
        return next(self.responses)


async def test_graph_revises_until_the_score_passes() -> None:
    graph = build_humanizer_graph(
        FakeWriter(["First draft.", "Natural final draft."]),
        FakeEvaluator(
            [
                Evaluation(score=70, feedback=["The opening feels generic."]),
                Evaluation(score=92, feedback=[]),
            ]
        ),
        score_threshold=85,
        max_passes=3,
    )

    result = await graph.ainvoke(
        {
            "original_text": "Source text.",
            "current_text": "Source text.",
            "audience": "general",
            "tone": "conversational",
            "feedback": [],
            "score": 0,
            "passes": 0,
        }
    )

    assert result["current_text"] == "Natural final draft."
    assert result["score"] == 92
    assert result["passes"] == 2


async def test_graph_stops_at_the_pass_limit() -> None:
    graph = build_humanizer_graph(
        FakeWriter(["Only draft."]),
        FakeEvaluator([Evaluation(score=25, feedback=["Still rough."])]),
        score_threshold=85,
        max_passes=1,
    )

    result = await graph.ainvoke(
        {
            "original_text": "Source text.",
            "current_text": "Source text.",
            "audience": "general",
            "tone": "conversational",
            "feedback": [],
            "score": 0,
            "passes": 0,
        }
    )

    assert result["score"] == 25
    assert result["passes"] == 1
