import pytest

from ndacheck.check import QUESTIONS, candidates, check, clauses, decide

NDA = ("1. Confidential Information includes all information disclosed in writing or orally. "
       "2. The Recipient shall use Confidential Information solely for the Purpose. "
       "3. The Recipient may disclose Confidential Information to its employees who need to know it. "
       "4. Upon termination, the Recipient shall return or destroy all Confidential Information. "
       "5. For one year the Recipient shall not solicit or hire any employee of the Discloser.")


def test_clauses_and_candidates():
    b = clauses(NDA)
    assert len(b) == 5
    c = candidates(NDA, b, "nda-18")
    assert "solicit" in NDA[c[0][0]:c[0][1]]  # best match first
    assert candidates(NDA, b, "nda-11") == []  # nothing about reverse engineering


def test_decide_thresholds_and_fallback():
    th = {"entail": 0.6, "contra": 0.7, "fallback": "NotMentioned"}
    assert decide([], th)[0] == "NotMentioned"
    assert decide([(0.9, 0.05), (0.2, 0.1)], th)[:2] == ("Entailment", 0)
    assert decide([(0.1, 0.8)], th)[:2] == ("Contradiction", 0)
    assert decide([(0.5, 0.5)], dict(th, fallback="Entailment")) == ("Entailment", 0, 0.5, False)


def test_every_question_has_a_keyword_rule():
    assert len(QUESTIONS) == 17 and all(len(v) == 3 for v in QUESTIONS.values())


@pytest.mark.slow
def test_real_model_end_to_end():
    answers = {a.question: a for a in check(NDA)}
    assert len(answers) == 17
    assert answers["nda-18"].label == "Entailment" and "solicit" in answers["nda-18"].evidence
    assert answers["nda-11"].label == "NotMentioned"
