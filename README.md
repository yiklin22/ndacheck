# ndacheck

Answers 17 standard questions about an NDA, with the clause behind each
answer: Does it have a non-solicit? Must information be marked to count?
Can you keep a copy after the end? Is independent development allowed?

**The business problem.** Small companies sign NDAs from customers, suppliers
and investors every week. Most are standard, a few hide a non-solicit or an
unlimited term, and a lawyer's review costs more than the deal is worth at
that stage. ndacheck gives a first pass in seconds: each answer comes with
the clause it was read from, so a person checks only the flagged points.

## How it works

1. Split the NDA into clauses.
2. For each question, keywords pick up to 4 candidate clauses. No match
   means "not mentioned".
3. An NLI model (`cross-encoder/nli-deberta-v3-base`, Apache-2.0, CPU)
   scores each clause: does it entail or contradict the question's statement?
4. Per-question thresholds, fitted on the ContractNLI train split, turn the
   scores into yes / no / not mentioned. Below threshold, the answer is the
   question's most common train-split answer.

```bash
uv venv && uv pip install torch transformers sentencepiece protobuf pytest
python -m ndacheck my_nda.txt          # or --json
pytest -q
```

## How well it works

| split | method | accuracy | macro-F1 | F1 yes | F1 no | F1 not mentioned |
|---|---|---|---|---|---|---|
| dev (61) | default thresholds (0.5), always "not mentioned" when unsure | 62.0% | 0.553 | 0.635 | 0.339 | 0.685 |
| dev (61) | thresholds + fallback fitted on train | 74.2% | 0.688 | 0.790 | 0.564 | 0.710 |
| dev (61) | most common train answer per question | 68.1% | 0.633 | 0.753 | 0.516 | 0.629 |
| **test (123)** | **thresholds + fallback fitted on train** | **73.8%** | **0.684** | 0.782 | 0.542 | 0.728 |
| test (123) | most common train answer per question | 65.9% | 0.617 | 0.730 | 0.506 | 0.614 |

Test was run once, after thresholds were fitted on train and checked on
dev. Per question (`docs/results-test.md`), ndacheck beats the baseline on
15 of 17, ties on "sharing with third parties", and is behind on "limited
use" (80% vs 84%). Biggest gains: "keeping a copy after the end" (57% vs
24%), "verbal information" (80% vs 59%), "independent development" (74% vs
59%). When a yes/no answer is right, its quoted clause is one the
annotators marked 74% of the time.

What the numbers mean:

- **The first version was worse than guessing.** With untuned thresholds the
  model lost to "always give the usual answer" (62.0% vs 68.1% on dev).
  Fitting thresholds per question on train, and falling back to the usual
  answer when unsure, is what moved it above the baseline.
- **"No" answers are the weak spot** (F1 0.54). Those are the ones a
  business cares most about ("the NDA forbids copies"), so they must be read
  by a person.
- **Low-confidence answers are marked.** When no clause clears the
  threshold, the CLI says "usual answer for NDAs; no clear clause, check"
  and shows no quote, instead of pointing at an unrelated clause.
- **Tried and dropped:** keyword rules that force "no" ("whether or not
  marked", "shall not copy", "without retaining any copies"), switched on per
  question only when they helped on train. They raised train accuracy
  (76.0% -> 76.4%) but lowered dev (74.2% -> 73.8%), so they were removed
  (kept in `git stash` as "dropped contradiction-rule experiment").
- The ContractNLI paper's models were trained on this data; this is an
  off-the-shelf NLI model plus fitted thresholds, so it is not comparable to
  their numbers and is likely below them.

## Data

[ContractNLI](https://stanfordnlp.github.io/contract-nli/) (Koreeda and
Manning, 2021; CC BY 4.0): 607 NDAs from EDGAR and the web, each annotated
for 17 hypotheses as Entailment, Contradiction or NotMentioned, with evidence
spans. Splits: 423 train, 61 dev, 123 test.

```bash
mkdir -p data/raw && cd data/raw
curl -L -o contract-nli.zip https://stanfordnlp.github.io/contract-nli/resources/contract-nli.zip && unzip contract-nli.zip
cd ../.. && python scripts/evaluate.py --split train --tune && python scripts/evaluate.py --split dev && python scripts/evaluate.py --split test
```
