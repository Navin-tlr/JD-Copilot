import sys
from types import SimpleNamespace

import pytest

pytest.importorskip("pydantic")

class _RequestsStub(SimpleNamespace):
    @staticmethod
    def post(*args, **kwargs):
        raise RuntimeError("requests.post should not be called during tests")


sys.modules.setdefault("requests", _RequestsStub())

from app.agent import decompose_multi_hop_query


def test_decompose_multi_hop_detects_two_questions():
    query = "How many companies came for placements, and what are the most sought after skills?"
    sub_questions = decompose_multi_hop_query(query)
    assert len(sub_questions) == 2
    assert sub_questions[0].lower().startswith("how many companies")
    assert sub_questions[0].endswith("?")
    assert sub_questions[1].lower().startswith("what are the most")
    assert sub_questions[1].endswith("?")


def test_decompose_multi_hop_detects_without_question_marks():
    query = "How many companies came for placements what are the most sought after skills"
    sub_questions = decompose_multi_hop_query(query)
    assert len(sub_questions) == 2
    assert sub_questions[0].lower().startswith("how many companies")
    assert sub_questions[0].endswith("?")
    assert sub_questions[1].lower().startswith("what are the most")
    assert sub_questions[1].endswith("?")


def test_decompose_multi_hop_single_question_passthrough():
    query = "What is the highest salary offered?"
    sub_questions = decompose_multi_hop_query(query)
    assert sub_questions == ["What is the highest salary offered?"]
