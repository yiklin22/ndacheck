"""Fine-tune an NLI cross-encoder on ContractNLI train (CPU is enough).

  python scripts/finetune.py --base cross-encoder/nli-deberta-v3-xsmall --out models/ft-xsmall --epochs 3

Trains on the (clause, hypothesis, label) pairs of ndacheck.finetune.build_pairs
from the train documents that are NOT in data/holdout-ids.json (a fixed 20%
of train, kept for fitting thresholds). Starts from the model's NLI head, so
the labels keep their meaning (0 contradiction, 1 entailment, 2 neutral).
Saves the model after every epoch to <out>/epoch-<n> and a log with wall time,
losses and model size to <out>/train-log.json. The weights stay local
(models/ is in .gitignore).
"""
import argparse
import collections
import json
import random
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ndacheck.finetune import LABEL_ID, build_pairs, holdout_ids, split_train  # noqa: E402

DATA = ROOT / "data/raw/contract-nli"
HOLDOUT = ROOT / "data/holdout-ids.json"


def batches(enc, labels, size, rng):
    """Shuffled batches of similar length (less padding, faster on CPU)."""
    order = list(range(len(labels)))
    rng.shuffle(order)
    chunks = [order[i:i + size * 50] for i in range(0, len(order), size * 50)]
    out = []
    for ch in chunks:
        ch.sort(key=lambda i: len(enc[i]))
        out += [ch[i:i + size] for i in range(0, len(ch), size)]
    rng.shuffle(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="cross-encoder/nli-deberta-v3-xsmall")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--threads", type=int, default=torch.get_num_threads())
    ap.add_argument("--max-steps", type=int, default=0, help="stop early (timing runs)")
    a = ap.parse_args()
    torch.manual_seed(a.seed)
    torch.set_num_threads(a.threads)
    rng = random.Random(a.seed)

    docs = json.load(open(DATA / "train.json"))["documents"]
    held = holdout_ids([d["id"] for d in docs])
    if HOLDOUT.exists():
        assert json.loads(HOLDOUT.read_text()) == held, f"{HOLDOUT} does not match holdout_ids()"
    else:
        HOLDOUT.write_text(json.dumps(held) + "\n")
    pairs = build_pairs(split_train(docs, held)[0])
    tok = AutoTokenizer.from_pretrained(a.base)
    model = AutoModelForSequenceClassification.from_pretrained(a.base)
    assert {v.lower(): k for k, v in model.config.id2label.items()} == \
        {"contradiction": 0, "entailment": 1, "neutral": 2}, model.config.id2label
    enc = tok([p for p, _, _ in pairs], [h for _, h, _ in pairs], truncation="only_first", max_length=a.max_length)["input_ids"]
    labels = [LABEL_ID[lab] for _, _, lab in pairs]
    steps_per_epoch = -(-len(pairs) // a.batch)
    total = a.max_steps or steps_per_epoch * a.epochs
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    sched = get_linear_schedule_with_warmup(opt, int(0.1 * total), total)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    log = {"base": a.base, "args": vars(a), "pairs": len(pairs), "labels": collections.Counter(lab for *_, lab in pairs),
           "finetune_docs": len(docs) - len(held), "holdout_docs": len(held),
           "parameters": sum(p.numel() for p in model.parameters()), "epochs": []}
    start, step = time.time(), 0
    for ep in range(1, a.epochs + 1):
        model.train()
        t0, cpu0, losses = time.time(), time.process_time(), []
        for b in batches(enc, labels, a.batch, rng):
            x = tok.pad({"input_ids": [enc[i] for i in b]}, return_tensors="pt")
            loss = model(**x, labels=torch.tensor([labels[i] for i in b])).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(), sched.step(), opt.zero_grad()
            losses.append(loss.item())
            step += 1
            if step % 50 == 0:
                print(f"epoch {ep} step {step}/{total} loss {sum(losses[-50:]) / 50:.4f} "
                      f"{time.time() - start:.0f}s", file=sys.stderr, flush=True)
            if step == total:
                break
        d = out / f"epoch-{ep}"
        model.save_pretrained(d)
        tok.save_pretrained(d)
        log["epochs"].append({"epoch": ep, "steps": len(losses), "mean_loss": sum(losses) / len(losses),
                              "wall_seconds": round(time.time() - t0, 1), "cpu_seconds": round(time.process_time() - cpu0, 1),
                              "size_mb": round(sum(f.stat().st_size for f in d.iterdir()) / 1e6, 1)})
        log["wall_seconds"] = round(time.time() - start, 1)
        (out / "train-log.json").write_text(json.dumps(log, indent=1))
        print(json.dumps(log["epochs"][-1]), file=sys.stderr, flush=True)
        if step == total:
            break


if __name__ == "__main__":
    main()
