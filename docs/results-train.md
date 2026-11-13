# ndacheck on ContractNLI train (423 NDAs, 7191 question answers)

| | accuracy | macro-F1 | F1 Entailment | F1 Contradiction | F1 NotMentioned |
|---|---|---|---|---|---|
| ndacheck | 76.0% | 0.704 | 0.808 | 0.560 | 0.744 |
| most common train label per question | 68.0% | 0.654 | 0.740 | 0.596 | 0.624 |

Evidence: when ndacheck answers yes/no correctly, its clause is one the annotators marked 76.9% of the time (3349 answers).

| question | ndacheck accuracy | baseline accuracy | gold yes / no / not mentioned |
|---|---|---|---|
| Explicit identification | 68% | 52% | 91 / 112 / 220 |
| Only technical information | 81% | 73% | 23 / 309 / 91 |
| Verbal information included | 80% | 64% | 270 / 4 / 149 |
| Limited use | 87% | 86% | 364 / 7 / 52 |
| Sharing with employees | 84% | 82% | 345 / 13 / 65 |
| Sharing with third parties | 63% | 61% | 259 / 111 / 53 |
| Notice on compelled disclosure | 78% | 65% | 276 / 0 / 147 |
| Confidentiality of the agreement | 76% | 62% | 159 / 2 / 262 |
| No reverse engineering | 93% | 86% | 59 / 1 / 363 |
| Independent development allowed | 71% | 62% | 263 / 0 / 160 |
| Getting similar information from others allowed | 81% | 74% | 311 / 0 / 112 |
| No licence granted | 80% | 77% | 327 / 0 / 96 |
| Return or destroy at the end | 71% | 57% | 181 / 1 / 241 |
| Copies allowed | 64% | 61% | 91 / 76 / 256 |
| No solicitation of staff | 88% | 78% | 93 / 0 / 330 |
| Obligations survive the end | 77% | 71% | 300 / 11 / 112 |
| Keeping a copy after the end allowed | 50% | 46% | 118 / 194 / 111 |
