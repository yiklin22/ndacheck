# ndacheck on ContractNLI test (123 NDAs, 2091 question answers)

| | accuracy | macro-F1 | F1 Entailment | F1 Contradiction | F1 NotMentioned |
|---|---|---|---|---|---|
| ndacheck | 74.1% | 0.685 | 0.787 | 0.538 | 0.729 |
| most common train label per question | 65.9% | 0.617 | 0.730 | 0.506 | 0.614 |

Evidence: when ndacheck answers yes/no correctly, its clause is one the annotators marked nan% of the time (910 answers).

| question | ndacheck accuracy | baseline accuracy | gold yes / no / not mentioned |
|---|---|---|---|
| Explicit identification | 55% | 51% | 24 / 36 / 63 |
| Only technical information | 76% | 72% | 6 / 88 / 29 |
| Verbal information included | 80% | 59% | 73 / 3 / 47 |
| Limited use | 80% | 84% | 103 / 7 / 13 |
| Sharing with employees | 79% | 76% | 93 / 1 / 29 |
| Sharing with third parties | 63% | 63% | 77 / 25 / 21 |
| Notice on compelled disclosure | 76% | 63% | 77 / 0 / 46 |
| Confidentiality of the agreement | 79% | 63% | 46 / 0 / 77 |
| No reverse engineering | 97% | 89% | 13 / 0 / 110 |
| Independent development allowed | 74% | 59% | 73 / 0 / 50 |
| Getting similar information from others allowed | 85% | 78% | 96 / 0 / 27 |
| No licence granted | 74% | 70% | 86 / 0 / 37 |
| Return or destroy at the end | 69% | 69% | 37 / 1 / 85 |
| Copies allowed | 64% | 60% | 24 / 25 / 74 |
| No solicitation of staff | 86% | 77% | 28 / 0 / 95 |
| Obligations survive the end | 67% | 64% | 79 / 4 / 40 |
| Keeping a copy after the end allowed | 57% | 24% | 33 / 30 / 60 |
