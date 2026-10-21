"""Apply explicit presentation-review decisions to a fingerprinted saved report.

Self-asserted reviewer IDs are for teaching audit shape, not authenticated human
identity. No review decision can rewrite artifact or safety acceptance results.
"""
import argparse
import copy
import json
from pathlib import Path
from .pipeline import release_gate, sha


def apply(report, report_bytes, decisions):
    if json.loads(report_bytes) != report:
        raise ValueError("report_object_does_not_match_fingerprint_bytes")
    if decisions.get("report_sha256") != sha(report_bytes):
        raise ValueError("review_targets_different_report")
    result = copy.deepcopy(report)
    rows = {r["id"]: r for r in result["rows"]}
    seen = set()
    for decision in decisions.get("decisions", []):
        sid = decision["sample_id"]
        if sid not in rows or sid in seen:
            raise ValueError("unknown_or_duplicate_review_id")
        seen.add(sid)
        if decision["decision"] not in {"accept_presentation", "reject_presentation"}:
            raise ValueError("review_cannot_override_task_or_safety")
        if not decision.get("reviewer") or not decision.get("rationale"):
            raise ValueError("review_needs_identity_and_rationale")
        candidate = rows[sid]["candidate"]
        if not candidate["review_pending"]:
            raise ValueError("sample_not_pending_review")
        candidate["review_pending"] = False
        if decision["decision"] == "reject_presentation":
            candidate["quality_pass"] = False
    result["review_audit"] = {"source_report_sha256": sha(report_bytes), "decisions": decisions["decisions"],
                             "identity_assurance": "self-asserted teaching identity, not authenticated"}
    result["gate"] = release_gate(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = args.report.read_bytes()
    reviewed = apply(json.loads(data), data, json.loads(args.decisions.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reviewed, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(reviewed["gate"], ensure_ascii=False))


if __name__ == "__main__":
    main()
