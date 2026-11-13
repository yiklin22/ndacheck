"""Score ndacheck on ContractNLI (Koreeda & Manning 2021, CC BY 4.0).

  python scripts/evaluate.py --split dev  [--tune]   # --tune: fit thresholds per question on dev
  python scripts/evaluate.py --split test             # uses ndacheck/thresholds.json

NLI scores are cached per (split, document, question, clause) in .cache, so
re-scoring with new thresholds is instant. Reports accuracy and macro-F1 over
the three labels, against always answering each question's most common
train-split label, and how often the evidence clause is one the annotators
marked.
"""
import argparse
import collections
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ndacheck.check import LABELS, QUESTIONS, candidates, clauses, decide, nli, thresholds  # noqa: E402

DATA = ROOT / "data/raw/contract-nli"


def load(split):
    d = json.load(open(DATA / f"{split}.json"))
    return d["documents"]


def scored(split):
    cache = ROOT / ".cache" / f"{split}-scores.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out = {}
    docs = load(split)
    for n, doc in enumerate(docs):
        text = doc["text"]
        bounds = clauses(text, doc["spans"])
        for q in QUESTIONS:
            c = candidates(text, bounds, q)
            idx = [bounds.index(b) for b in c]
            sc = nli([(text[s:e], QUESTIONS[q][1]) for s, e in c])
            out[f"{doc['id']}|{q}"] = {"spans": idx, "scores": sc}
        print(f"{n + 1}/{len(docs)}", file=sys.stderr, end="\r")
    cache.parent.mkdir(exist_ok=True)
    cache.write_text(json.dumps(out))
    return out


def f1s(gold, pred):
    out = {}
    for lab in LABELS:
        tp = sum(g == p == lab for g, p in zip(gold, pred))
        fp = sum(p == lab != g for g, p in zip(gold, pred))
        fn = sum(g == lab != p for g, p in zip(gold, pred))
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        out[lab] = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    return out


def run(docs, sc, th):
    rows = []
    for doc in docs:
        ann = doc["annotation_sets"][0]["annotations"]
        for q in QUESTIONS:
            r = sc[f"{doc['id']}|{q}"]
            if q not in th:
                continue
            label, i, _, _ = decide([tuple(x) for x in r["scores"]], th.get(q, th.get("default")))
            ev = r["spans"][i] if i is not None else None
            rows.append((q, ann[q]["choice"], label, ev, set(ann[q]["spans"])))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "dev", "test"], default="dev")
    ap.add_argument("--tune", action="store_true", help="fit thresholds per question on this split (use train)")
    a = ap.parse_args()
    docs, sc = load(a.split), scored(a.split)
    if a.tune:
        grid = [x / 20 for x in range(2, 20)] + [1.01]
        th = {}
        for q in QUESTIONS:
            best = None
            for te, tc, fb in itertools.product(grid, grid, LABELS):
                t = {q: {"entail": te, "contra": tc, "fallback": fb}}
                rows = [r for r in run(docs, sc, t) if r[0] == q]
                acc = sum(g == p for _, g, p, _, _ in rows)
                if best is None or acc > best[0]:
                    best = (acc, te, tc, fb)
            th[q] = {"entail": best[1], "contra": best[2], "fallback": best[3]}
        (ROOT / "ndacheck/thresholds.json").write_text(json.dumps(th, indent=1))
    th = thresholds()
    rows = run(docs, sc, th)
    train = load("train")
    major = {q: collections.Counter(d["annotation_sets"][0]["annotations"][q]["choice"] for d in train).most_common(1)[0][0]
             for q in QUESTIONS}
    gold = [g for _, g, _, _, _ in rows]
    pred = [p for _, _, p, _, _ in rows]
    base = [major[q] for q, _, _, _, _ in rows]
    acc = sum(g == p for g, p in zip(gold, pred)) / len(rows)
    bacc = sum(g == p for g, p in zip(gold, base)) / len(rows)
    f, bf = f1s(gold, pred), f1s(gold, base)
    ev_rows = [(ev, gs) for _, g, p, ev, gs in rows if p == g and p != "NotMentioned"]
    ev_hit = sum(ev in gs for ev, gs in ev_rows) / max(1, len(ev_rows))
    lines = [f"# ndacheck on ContractNLI {a.split} ({len(docs)} NDAs, {len(rows)} question answers)", "",
             "| | accuracy | macro-F1 | F1 Entailment | F1 Contradiction | F1 NotMentioned |", "|---|---|---|---|---|---|",
             f"| ndacheck | {acc:.1%} | {sum(f.values()) / 3:.3f} | {f['Entailment']:.3f} | {f['Contradiction']:.3f} | {f['NotMentioned']:.3f} |",
             f"| most common train label per question | {bacc:.1%} | {sum(bf.values()) / 3:.3f} | {bf['Entailment']:.3f} | {bf['Contradiction']:.3f} | {bf['NotMentioned']:.3f} |",
             "", f"Evidence: when ndacheck answers yes/no correctly, its clause is one the annotators marked {ev_hit:.1%} of the time ({len(ev_rows)} answers).",
             "", "| question | ndacheck accuracy | baseline accuracy | gold yes / no / not mentioned |", "|---|---|---|---|"]
    for q, (name, _, _) in QUESTIONS.items():
        rq = [r for r in rows if r[0] == q]
        n = len(rq)
        c = collections.Counter(g for _, g, _, _, _ in rq)
        lines.append(f"| {name} | {sum(g == p for _, g, p, _, _ in rq) / n:.0%} | {sum(g == major[q] for _, g, _, _, _ in rq) / n:.0%} | "
                     f"{c['Entailment']} / {c['Contradiction']} / {c['NotMentioned']} |")
    out = "\n".join(lines) + "\n"
    print(out)
    (ROOT / f"docs/results-{a.split}.md").write_text(out)


if __name__ == "__main__":
    main()
