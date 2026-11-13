"""Training pairs for fine-tuning the NLI model on ContractNLI train.

Each pair is (clause, hypothesis, label):
  Entailment / Contradiction - every annotated evidence span of the document
  NotMentioned               - the question's top keyword candidates
                               (ndacheck.check.candidates), as the pipeline
                               would score them

A fixed 20% of the train documents is held out from fine-tuning, so that the
thresholds can later be fitted on documents the model never saw.
"""
from __future__ import annotations

import random

from .check import QUESTIONS, candidates

# Same label order as the cross-encoder NLI models' heads.
LABEL_ID = {"Contradiction": 0, "Entailment": 1, "NotMentioned": 2}


def holdout_ids(ids, frac: float = 0.2, seed: int = 13) -> list[int]:
    """A reproducible random `frac` of the document ids, sorted."""
    ids = sorted(ids)
    return sorted(random.Random(seed).sample(ids, round(frac * len(ids))))


def split_train(docs, held_ids) -> tuple[list, list]:
    """(fine-tune documents, held-out documents) by document id."""
    held = set(held_ids)
    return [d for d in docs if d["id"] not in held], [d for d in docs if d["id"] in held]


def build_pairs(docs, k: int = 4) -> list[tuple[str, str, str]]:
    """(clause, hypothesis, label) pairs from ContractNLI documents."""
    out = []
    for doc in docs:
        text, bounds = doc["text"], [tuple(s) for s in doc["spans"]]
        ann = doc["annotation_sets"][0]["annotations"]
        for q, (_, hyp, _) in QUESTIONS.items():
            label = ann[q]["choice"]
            if label == "NotMentioned":
                idx = [bounds.index(b) for b in candidates(text, bounds, q, k)]
            else:
                idx = ann[q]["spans"]
            for i in idx:
                s, e = bounds[i]
                out.append((text[s:e].strip(), hyp, label))
    return out
