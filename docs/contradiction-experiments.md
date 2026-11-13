# Why "No" answers are weak, and three fixes that did not hold up

All numbers on this page come from train and dev only. The test split was
not used to choose anything.

The fix ideas came from reading the dev errors below, so dev is not a fully
clean check for them (the keyword coverage figures were measured on train).
That would matter for a fix that was kept; none was.

## Error analysis (dev, shipped system)

Dev has 95 gold "No" (Contradiction) answers. The shipped system gets 44
right and misses 51. It also says "No" 17 times when the gold answer is
"yes" (6) or "not mentioned" (11).

| why a gold "No" was missed | count |
|---|---|
| no candidate clause at all (keywords matched nothing) | 7 |
| candidates found, but none is an annotated clause | 13 |
| annotated clause found, model unsure, fell back to the usual answer ("not mentioned") | 13 |
| annotated clause found, model unsure, fell back to the usual answer ("yes") | 12 |
| annotated clause found, model confidently said "yes" | 6 |

So 20 misses are retrieval (wrong or no clauses) and 31 are labelling. By
question, the misses concentrate in "Sharing with third parties" (14 of 14
gold "No" missed), "Keeping a copy after the end" (9 of 12), "Explicit
identification" (8 of 10) and "Copies allowed" (8 of 8).

Two causes stand out when reading the cases:

1. **The NLI model does not read a prohibition as contradicting a
   permission.** For "shall not disclose ... to any third party" against
   "Receiving Party may share some Confidential Information with some
   third-parties", the off-the-shelf model gives contradiction scores near
   0.0; the same holds for "shall not copy" against "may create a copy ... in
   some circumstances".
2. **Keywords miss the "No" clauses of "Keeping a copy after the end".** The
   annotated clauses are "return all copies" clauses that never say "retain"
   or "archive". On train, the keywords reach an annotated clause for 42 of
   194 gold "No" answers on this question (67 of 111 for "Sharing with third
   parties").

## Fixes tried (each fitted on train, judged on dev)

Kept only if dev improves overall and on Contradiction. None did, so the
shipped system is unchanged.

| | train acc | train macro-F1 | train F1 No | dev acc | dev macro-F1 | dev F1 yes | dev F1 No | dev F1 not mentioned |
|---|---|---|---|---|---|---|---|---|
| shipped system | 76.0% | 0.704 | 0.560 | **74.2%** | **0.688** | 0.790 | **0.564** | 0.710 |
| 1. opposite statement as a second hypothesis | 76.0% | 0.705 | 0.563 | 74.0% | 0.682 | 0.789 | 0.549 | 0.709 |
| 2. fix 1 + wider keywords for third parties / keeping a copy | 76.4% | 0.733 | 0.648 | 72.5% | 0.664 | 0.789 | 0.513 | 0.690 |
| 3. fix 1 + "yes" wins whenever a permission clause clears its threshold | 76.6% | 0.709 | 0.563 | 74.0% | 0.682 | 0.788 | 0.549 | 0.710 |

1. **Opposite statement.** For five questions, a second statement that means
   "no" (e.g. "Receiving Party shall not disclose Confidential Information to
   any third party."); a clause that entails it counts as contradiction
   evidence, switched on per question when it helped on train. Train turned
   it on only for "Explicit identification" and "Only technical information".
   It cannot separate the classes for the others because almost every NDA
   has the prohibition: on train, the opposite statement scores above 0.5 in
   66% of "yes" and 61% of "No" documents for third parties, and 78% vs 83%
   for copies. The gold "No" depends on whether a permission exists
   elsewhere in the document, which a per-clause score does not see.
2. **Wider keywords.** Adding "copies / return / destroy / deliver" to
   "Keeping a copy after the end" raises train retrieval of annotated "No"
   clauses from 42/194 to 190/194; adding "any person / to anyone / only to
   its / need to know" to third parties raises it from 67/111 to 82/111.
   Train F1 for "No" rose from 0.563 to 0.648, but dev fell (74.2% -> 72.5%,
   F1 No 0.564 -> 0.513): the extra thresholds overfit train.
3. **Permission first.** A per-question switch, fitted on train, that answers
   "yes" whenever the best permission clause clears its threshold, even if a
   prohibition scores higher, so that "No" means "prohibition found and no
   permission found". Scored on the cached fix-1 scores; it raised train but
   left dev where fix 1 was.

A fine-tuned model was not tried. Train has 16,655 candidate clause pairs,
and a training step costs several times a scoring step; on this CPU-only
machine one epoch would take hours. It is the most likely real fix, because the problem is document-level
(a prohibition and no exception anywhere), which is what the ContractNLI
paper's trained models learn.

The code is on the local branch `experiment/contradiction-fixes`: tag
`exp-fix1-fix3` is fix 1 (run `scripts/evaluate.py --split train --tune`, then
`--split dev`) and fix 3 (`scripts/exp_entail_first.py out.json`); tag
`exp-fix2` is fix 2. Fixes 1 and 3 were re-run from their tag and reproduce
the table; fix 2's dev row was re-run on its tree before it was committed.
