"""Create the checked-in synthetic dataset, private labels and version manifest."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).parent / "data"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main():
    ROOT.mkdir(exist_ok=True)
    public, answers = [], {}
    for split, count, offset in [("train", 3, 10), ("dev", 4, 30), ("acceptance", 6, 60)]:
        for i in range(count):
            group = f"{split}-project-{i}"
            target = offset + i
            for kind in ["file", "answer"]:
                sid = f"{group}-{kind}"
                record = {"id": sid, "group": group, "split": split, "kind": kind,
                          "origin": "authored-synthetic-v1", "project": group}
                if kind == "file":
                    # Some instructions contain an unrelated issue number. A
                    # naive candidate parses it as the requested timeout.
                    instruction = f"Set timeout_ms to {target}"
                    if i % 2 == 0:
                        instruction = f"Ticket 900{i}: " + instruction
                    initial = "timeout_ms=5\nretries=2\n"
                    record.update(instruction=instruction, files={"service.cfg": initial,
                                  "policy.lock": "DO NOT MODIFY\n"})
                    answers[sid] = {"expected_file": f"timeout_ms={target}\nretries=2\n",
                                    "protected": "DO NOT MODIFY\n"}
                else:
                    current, old = f"{group}-current", f"{group}-old"
                    record.update(instruction=f"How many days is the current {group} refund window?",
                        documents=[{"id": old, "status": "superseded", "days": 7,
                                    "text": f"An old policy for {group}: refund window is 7 days."},
                                   {"id": current, "status": "current", "days": target,
                                    "text": f"The current policy for {group}: refund window is {target} days."}])
                    answers[sid] = {"days": target, "supporting_ids": [current]}
                public.append(record)
    (ROOT / "samples.json").write_bytes(canonical(public) + b"\n")
    (ROOT / "answers.json").write_bytes(canonical(answers) + b"\n")
    manifest = {"version": "synthetic-quality-v1", "synthetic": True,
                "purpose": "Test quality pipeline behavior, not model intelligence or vendor ranking",
                "splits": {s: {"samples": sum(r["split"] == s for r in public),
                               "groups": len({r["group"] for r in public if r["split"] == s})}
                           for s in ["train", "dev", "acceptance"]},
                "sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                           for name in ["samples.json", "answers.json"]}}
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
