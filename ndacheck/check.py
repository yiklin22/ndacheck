"""Check an NDA against 17 standard questions (the ContractNLI hypotheses).

For each question: keywords pick the candidate clauses, an NLI model
(cross-encoder/nli-deberta-v3-base, Apache-2.0, CPU) scores each clause as
entailing or contradicting the question's statement, and thresholds tuned on
the ContractNLI train split turn the best scores into one answer:

  yes  (Entailment)    - the NDA says it, with the clause as evidence
  no   (Contradiction) - the NDA says the opposite
  not mentioned

Questions whose keywords match no clause are "not mentioned" without running
the model.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

# id: (short name, hypothesis, keyword regex)
QUESTIONS = {
    "nda-1": ("Explicit identification", "All Confidential Information shall be expressly identified by the Disclosing Party.",
              r"mark|label|designat|identif|legend|reduced to writing|confirm(?:ed)? in writing|summar"),
    "nda-2": ("Only technical information", "Confidential Information shall only include technical information.",
              r"technical|business|financial|commercial|marketing|customer|information of any (?:kind|nature)"),
    "nda-3": ("Verbal information included", "Confidential Information may include verbally conveyed information.",
              r"\boral|verbal|visual|spoken"),
    "nda-4": ("Limited use", "Receiving Party shall not use any Confidential Information for any purpose other than the purposes stated in Agreement.",
              r"purpose|solely|exclusively|only (?:for|to)|use (?:of )?(?:the )?confidential|for no other"),
    "nda-5": ("Sharing with employees", "Receiving Party may share some Confidential Information with some of Receiving Party's employees.",
              r"employee|officer|director|staff|need to know|representative|personnel"),
    "nda-7": ("Sharing with third parties", "Receiving Party may share some Confidential Information with some third-parties (including consultants, agents and professional advisors).",
              r"third part|consultant|advis[eo]r|agent|contractor|affiliate|representative|attorney|accountant|counsel"),
    "nda-8": ("Notice on compelled disclosure", "Receiving Party shall notify Disclosing Party in case Receiving Party is required by law, regulation or judicial process to disclose any Confidential Information.",
              r"required by law|subpoena|court|compel|legal process|government|regulat|judicial|order of"),
    "nda-10": ("Confidentiality of the agreement", "Receiving Party shall not disclose the fact that Agreement was agreed or negotiated.",
               r"existence|terms of this agreement|fact that|negotiat|discussions|the transaction"),
    "nda-11": ("No reverse engineering", "Receiving Party shall not reverse engineer any objects which embody Disclosing Party's Confidential Information.",
               r"reverse[- ]engineer|decompil|disassembl|analy[sz]|chemical|composition"),
    "nda-12": ("Independent development allowed", "Receiving Party may independently develop information similar to Confidential Information.",
               r"independent(?:ly)? develop|develop(?:ed|s)? independently|similar|compet"),
    "nda-13": ("Getting similar information from others allowed", "Receiving Party may acquire information similar to Confidential Information from a third party.",
               r"third part|lawfully|rightfully|without (?:a )?(?:breach|restriction|obligation)|from (?:a|any) (?:source|third)"),
    "nda-15": ("No licence granted", "Agreement shall not grant Receiving Party any right to Confidential Information.",
               r"licen[cs]e|no right|any right|title|ownership|property of|intellectual property"),
    "nda-16": ("Return or destroy at the end", "Receiving Party shall destroy or return some Confidential Information upon the termination of Agreement.",
               r"return|destroy|destruction|delet|eras"),
    "nda-17": ("Copies allowed", "Receiving Party may create a copy of some Confidential Information in some circumstances.",
               r"\bcop(?:y|ies|ying)|reproduc|duplicat"),
    "nda-18": ("No solicitation of staff", "Receiving Party shall not solicit some of Disclosing Party's representatives.",
               r"solicit|\bhire|employ|recruit|entice"),
    "nda-19": ("Obligations survive the end", "Some obligations of Agreement may survive termination of Agreement.",
               r"surviv|termination|expir|period of|years? (?:after|from|following)|in perpetuity|remain in effect"),
    "nda-20": ("Keeping a copy after the end allowed", "Receiving Party may retain some Confidential Information even after the return or destruction of Confidential Information.",
               r"retain|archiv|back-?up|keep (?:one|a) cop|legal(?:ly)? (?:purposes|requir)|automatic(?:ally)?"),
}
LABELS = ("Entailment", "Contradiction", "NotMentioned")
THRESHOLDS_FILE = Path(__file__).with_name("thresholds.json")
DEFAULT_THRESHOLDS = {"entail": 0.5, "contra": 0.5}


@dataclass
class Answer:
    question: str
    name: str
    label: str
    evidence: str | None
    score: float
    confident: bool = True  # False: the question's usual answer, no clear clause found


def clauses(text: str, spans: list[tuple[int, int]] | None = None) -> list[tuple[int, int]]:
    """Clause boundaries: given spans (ContractNLI provides them) or rough sentences."""
    if spans:
        return [tuple(s) for s in spans]
    out, start = [], 0
    # Split after sentence ends, not after a clause number ("1. ").
    for m in re.finditer(r"(?<=[a-z)\]\"'][.;:])\s+(?=[A-Z(\d])|\n\s*\n", text):
        if m.start() > start:
            out.append((start, m.start()))
        start = m.end()
    if start < len(text):
        out.append((start, len(text)))
    return out


def candidates(text: str, bounds, qid: str, k: int = 4) -> list[tuple[int, int]]:
    rx = re.compile(QUESTIONS[qid][2], re.I)
    scored = []
    for s, e in bounds:
        n = len(rx.findall(text[s:e]))
        if n:
            scored.append((n, s, e))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [(s, e) for _, s, e in scored[:k]]


_MODEL = None


def _model():
    global _MODEL
    if _MODEL is None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        name = "cross-encoder/nli-deberta-v3-base"
        tok = AutoTokenizer.from_pretrained(name)
        model = AutoModelForSequenceClassification.from_pretrained(name).eval()
        _MODEL = (tok, model, torch)
    return _MODEL


def nli(pairs: list[tuple[str, str]], batch: int = 16) -> list[tuple[float, float]]:
    """(premise, hypothesis) -> (entailment, contradiction) probabilities."""
    if not pairs:
        return []
    tok, model, torch = _model()
    out = []
    with torch.inference_mode():
        for i in range(0, len(pairs), batch):
            chunk = pairs[i:i + batch]
            enc = tok([p for p, _ in chunk], [h for _, h in chunk], truncation="only_first", max_length=384,
                      padding=True, return_tensors="pt")
            probs = model(**enc).logits.softmax(-1).tolist()
            out += [(p[1], p[0]) for p in probs]  # labels: 0 contradiction, 1 entailment, 2 neutral
    return out


def decide(scores: list[tuple[float, float]], th: dict) -> tuple[str, int | None, float, bool]:
    """Pick the answer from the candidates' (entail, contra) scores:
    (label, index of the evidence clause, score, confident)."""
    if not scores:
        return "NotMentioned", None, 0.0, True
    ie = max(range(len(scores)), key=lambda i: scores[i][0])
    ic = max(range(len(scores)), key=lambda i: scores[i][1])
    e, c = scores[ie][0], scores[ic][1]
    if e >= th["entail"] and e >= c:
        return "Entailment", ie, e, True
    if c >= th["contra"]:
        return "Contradiction", ic, c, True
    # Not confident either way: the question's usual answer (from the train
    # split), with the best clause as a pointer when that answer is yes/no.
    fallback = th.get("fallback", "NotMentioned")
    idx = {"Entailment": ie, "Contradiction": ic}.get(fallback)
    return fallback, idx, max(e, c), False


def thresholds() -> dict:
    if THRESHOLDS_FILE.exists():
        return json.loads(THRESHOLDS_FILE.read_text())
    return {q: dict(DEFAULT_THRESHOLDS) for q in QUESTIONS}


def check(text: str, spans=None) -> list[Answer]:
    bounds = clauses(text, spans)
    th = thresholds()
    cands = {q: candidates(text, bounds, q) for q in QUESTIONS}
    pairs = [(text[s:e], QUESTIONS[q][1]) for q in QUESTIONS for s, e in cands[q]]
    scores = iter(nli(pairs))
    out = []
    for q, (name, _, _) in QUESTIONS.items():
        sc = [next(scores) for _ in cands[q]]
        label, idx, score, sure = decide(sc, th.get(q, DEFAULT_THRESHOLDS))
        ev = None if idx is None or not sure else text[cands[q][idx][0]:cands[q][idx][1]].strip()
        out.append(Answer(q, name, label, ev, round(score, 3), sure))
    return out
