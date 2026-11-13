"""python -m ndacheck <nda.txt> [--json]  - answer the 17 questions for one NDA."""
import json
import sys

from .check import check

SAY = {"Entailment": "yes", "Contradiction": "NO (says the opposite)", "NotMentioned": "not mentioned"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__)
        return 2
    text = open(argv[0], encoding="utf-8", errors="replace").read()
    answers = check(text)
    if "--json" in argv:
        print(json.dumps([a.__dict__ for a in answers], indent=1))
        return 0
    for a in answers:
        note = "" if a.confident else "  (usual answer for NDAs; no clear clause, check)"
        print(f"{a.name:<48} {SAY[a.label]}{note}")
        if a.evidence:
            ev = " ".join(a.evidence.split())
            print(f"    \"{ev[:200]}{'...' if len(ev) > 200 else ''}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
