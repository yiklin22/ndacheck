from ndacheck.check import QUESTIONS
from ndacheck.finetune import LABEL_ID, build_pairs, holdout_ids, split_train

TEXT = ("The Recipient may disclose information to its employees. "
        "The Recipient shall not solicit any employee of the Discloser. "
        "This Agreement is governed by the laws of Texas.")


def doc(choices):
    """One fake ContractNLI document; questions not in `choices` are NotMentioned with no spans."""
    s1 = TEXT.index("The Recipient shall")
    s2 = TEXT.index("This Agreement")
    ann = {q: {"choice": "NotMentioned", "spans": []} for q in QUESTIONS}
    ann.update(choices)
    return {"id": 1, "text": TEXT, "spans": [[0, s1 - 1], [s1, s2 - 1], [s2, len(TEXT)]],
            "annotation_sets": [{"annotations": ann}]}


def test_evidence_spans_become_entailment_and_contradiction():
    pairs = build_pairs([doc({"nda-5": {"choice": "Entailment", "spans": [0]},
                              "nda-18": {"choice": "Contradiction", "spans": [1, 2]}})])
    hyp5, hyp18 = QUESTIONS["nda-5"][1], QUESTIONS["nda-18"][1]
    assert ("The Recipient may disclose information to its employees.", hyp5, "Entailment") in pairs
    assert [p for p in pairs if p[1] == hyp18] == [
        ("The Recipient shall not solicit any employee of the Discloser.", hyp18, "Contradiction"),
        ("This Agreement is governed by the laws of Texas.", hyp18, "Contradiction")]


def test_not_mentioned_uses_keyword_candidates_only():
    pairs = build_pairs([doc({})])
    assert {p[2] for p in pairs} == {"NotMentioned"}
    # "employee" matches the employee-sharing keywords in clauses 0 and 1, not clause 2.
    assert [p[0] for p in pairs if p[1] == QUESTIONS["nda-5"][1]] == [
        "The Recipient may disclose information to its employees.",
        "The Recipient shall not solicit any employee of the Discloser."]
    # No keyword match (reverse engineering): no pair at all.
    assert not [p for p in pairs if p[1] == QUESTIONS["nda-11"][1]]
    assert len([p for p in pairs if p[1] == QUESTIONS["nda-5"][1]]) <= 4


def test_holdout_is_reproducible_and_20_percent():
    ids = list(range(100, 523))
    h = holdout_ids(ids)
    assert h == holdout_ids(list(reversed(ids))) == sorted(h)
    assert len(h) == 85 and set(h) <= set(ids)
    assert holdout_ids(ids, seed=14) != h


def test_label_ids_match_the_nli_head():
    assert LABEL_ID == {"Contradiction": 0, "Entailment": 1, "NotMentioned": 2}


def test_split_train_keeps_held_out_documents_apart():
    docs = [{"id": i} for i in range(10)]
    ft, held = split_train(docs, [2, 5])
    assert [d["id"] for d in held] == [2, 5]
    assert [d["id"] for d in ft] == [0, 1, 3, 4, 6, 7, 8, 9]
