# ndacheck on ContractNLI dev (61 NDAs, 1037 question answers)

| | accuracy | macro-F1 | F1 Entailment | F1 Contradiction | F1 NotMentioned |
|---|---|---|---|---|---|
| ndacheck | 74.5% | 0.689 | 0.796 | 0.561 | 0.711 |
| most common train label per question | 68.1% | 0.633 | 0.753 | 0.516 | 0.629 |

Evidence: when ndacheck answers yes/no correctly, its clause is one the annotators marked nan% of the time (488 answers).

| question | ndacheck accuracy | baseline accuracy | gold yes / no / not mentioned |
|---|---|---|---|
| Explicit identification | 64% | 52% | 19 / 10 / 32 |
| Only technical information | 74% | 72% | 6 / 44 / 11 |
| Verbal information included | 79% | 74% | 45 / 0 / 16 |
| Limited use | 79% | 82% | 50 / 3 / 8 |
| Sharing with employees | 92% | 89% | 54 / 2 / 5 |
| Sharing with third parties | 66% | 64% | 39 / 14 / 8 |
| Notice on compelled disclosure | 80% | 74% | 45 / 0 / 16 |
| Confidentiality of the agreement | 70% | 52% | 29 / 0 / 32 |
| No reverse engineering | 95% | 87% | 8 / 0 / 53 |
| Independent development allowed | 72% | 66% | 40 / 0 / 21 |
| Getting similar information from others allowed | 84% | 77% | 47 / 0 / 14 |
| No licence granted | 66% | 64% | 39 / 0 / 22 |
| Return or destroy at the end | 67% | 61% | 22 / 2 / 37 |
| Copies allowed | 70% | 72% | 9 / 8 / 44 |
| No solicitation of staff | 85% | 82% | 11 / 0 / 50 |
| Obligations survive the end | 67% | 70% | 43 / 0 / 18 |
| Keeping a copy after the end allowed | 57% | 20% | 13 / 12 / 36 |
