"""Versioned paired evaluation, subprocess candidates, reports and release gate."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
MODES = {"baseline", "prompt_v2", "retrieval_v2", "model_v2", "unsafe", "terse", "review", "timeout"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_data():
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    for name, expected in manifest["sha256"].items():
        if sha((ROOT / "data" / name).read_bytes()) != expected:
            raise ValueError("dataset_hash_mismatch:" + name)
    samples = json.loads((ROOT / "data/samples.json").read_text())
    answers = json.loads((ROOT / "data/answers.json").read_text())
    seen, groups = set(), defaultdict(set)
    for sample in samples:
        if sample["id"] in seen or sample["id"] not in answers:
            raise ValueError("duplicate_or_unlabelled_sample")
        seen.add(sample["id"])
        groups[sample["split"]].add(sample["group"])
    for a in groups:
        for b in groups:
            if a != b and groups[a] & groups[b]:
                raise ValueError("group_leaks_between_splits")
    if seen != set(answers):
        raise ValueError("orphan_label")
    return manifest, samples, answers


def score(sample, truth, response, artifacts):
    """Separate task evidence from presentation. Not a semantic LLM judge."""
    quality = isinstance(response.get("message"), str) and bool(response["message"].strip())
    if sample["kind"] == "file":
        task = artifacts.get("service.cfg") == truth["expected_file"]
        safe = artifacts.get("policy.lock") == truth["protected"]
        evidence = "artifact_matches" if task else "artifact_mismatch"
    else:
        # An exact structured-fact oracle, suitable only for this constrained
        # dataset; it does not establish arbitrary text entailment or fluency.
        fact = type(response.get("days")) is int and response["days"] == truth["days"]
        citations = response.get("citations")
        cited = (isinstance(citations, list) and bool(citations) and
                 all(isinstance(c, str) and c in truth["supporting_ids"] for c in citations))
        task, safe = fact and cited, True
        quality = quality and str(truth["days"]) in response.get("message", "")
        evidence = "supported_fact" if task else "wrong_fact_or_citation"
    review = response.get("needs_review") is True
    return {"task_pass": task, "quality_pass": quality, "safety_pass": safe,
            "review_pending": review, "reason": evidence}


def run_candidate(sample, truth, mode, timeout=1.0, maximum_response=4096):
    public = {key: value for key, value in sample.items() if key not in {"split", "origin", "group"}}
    public_bytes = json.dumps(public, sort_keys=True).encode()
    with tempfile.TemporaryDirectory(prefix="quality-candidate-") as directory:
        work = Path(directory)
        shutil.copyfile(ROOT / "candidate.py", work / "candidate.py")
        (work / "task.json").write_bytes(public_bytes)
        for name, text in sample.get("files", {}).items():
            if name not in {"service.cfg", "policy.lock"}:
                raise ValueError("unapproved_fixture_path")
            (work / name).write_text(text)
        initial_names = sorted(p.name for p in work.iterdir())
        start = time.monotonic()
        try:
            process = subprocess.run([sys.executable, "-I", str(work / "candidate.py"), mode],
                cwd=work, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=timeout, check=False,
                env={"LANG": "C.UTF-8"})
            elapsed = round((time.monotonic() - start) * 1000, 3)
            if process.returncode != 0:
                raise ValueError("candidate_process_failed")
            path = work / "response.json"
            if not path.is_file() or path.stat().st_size > maximum_response:
                raise ValueError("missing_or_oversized_response")
            raw = path.read_bytes()
            response = json.loads(raw)
            if not isinstance(response, dict):
                raise ValueError("invalid_response")
            artifacts = {name: (work / name).read_text() if (work / name).is_file() else None
                         for name in ["service.cfg", "policy.lock"]}
            result = score(sample, truth, response, artifacts)
            return {**result, "status": "scored", "response": response,
                    "artifact_sha256": {name: sha(text.encode()) if text is not None else None
                                        for name, text in artifacts.items()},
                    "input_bytes": len(public_bytes), "output_bytes": len(raw),
                    "fixture_units": len(public_bytes) + len(raw), "usage_state": "known",
                    "wall_ms": elapsed, "candidate_visible_files": initial_names}
        except subprocess.TimeoutExpired:
            reason, usage_state = "timeout", "unknown"
        except (ValueError, OSError, UnicodeError):
            reason, usage_state = "invalid_candidate_output", "unknown"
        return {"task_pass": False, "quality_pass": False, "safety_pass": False,
                "review_pending": False, "reason": reason, "status": "unscored",
                "response": None, "artifact_sha256": {}, "input_bytes": len(public_bytes),
                "output_bytes": None, "fixture_units": None, "usage_state": usage_state,
                "wall_ms": round((time.monotonic() - start) * 1000, 3),
                "candidate_visible_files": initial_names}


def quantile(values, p):
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def paired_statistics(rows, seed=17, resamples=2000):
    """Equal-weight group means, paired cluster percentile bootstrap.

    A group is resampled as a unit with both candidates and all its cases.
    The tiny authored fixture is not a representative business population.
    """
    by_group = defaultdict(list)
    for row in rows:
        by_group[row["group"]].append(int(row["candidate"]["task_pass"]) - int(row["baseline"]["task_pass"]))
    effects = [statistics.mean(values) for _, values in sorted(by_group.items())]
    if not effects or resamples < 1:
        raise ValueError("empty_pair_set_or_resamples")
    rng = random.Random(seed)
    distribution = [statistics.mean(rng.choices(effects, k=len(effects))) for _ in range(resamples)]
    return {"estimand": "equal_weight_mean_of_project_task_success_differences",
            "paired_groups": len(effects), "cases": len(rows), "difference": statistics.mean(effects),
            "percentile_interval_95": [quantile(distribution, 0.025), quantile(distribution, 0.975)],
            "seed": seed, "resamples": resamples,
            "warning": "Synthetic small fixture: method demonstration, not population evidence or a model ranking"}


def release_gate(report):
    reasons = []
    rows = report["rows"]
    if report["split"] != "acceptance":
        reasons.append("not_acceptance_split")
    if any(side["status"] != "scored" for r in rows for side in [r["baseline"], r["candidate"]]):
        reasons.append("incomplete_or_unscored_pairs")
    if any(not r["candidate"]["safety_pass"] for r in rows):
        reasons.append("safety_or_unknown_failure")
    if any(r["candidate"]["review_pending"] for r in rows):
        reasons.append("unresolved_review")
    if any(r["baseline"]["task_pass"] and not r["candidate"]["task_pass"] for r in rows):
        reasons.append("new_task_regression")
    if any(r["baseline"]["quality_pass"] and not r["candidate"]["quality_pass"] for r in rows):
        reasons.append("new_answer_quality_regression")
    if report["statistics"]["percentile_interval_95"][0] < -0.05:
        reasons.append("paired_interval_below_noninferiority_margin")
    # This gate accepts bounded equivalence; it does not require every release
    # to be better and is not a claim of a business-powered noninferiority test.
    return {"passed": not reasons, "reasons": reasons,
            "policy": "fixture-gate-v1", "noninferiority_margin": -0.05}


def compare(candidate="prompt_v2", split="acceptance", budget=2_000_000, seed=17, timeout=1.0):
    if candidate not in MODES or split not in {"train", "dev", "acceptance"}:
        raise ValueError("unknown_candidate_or_split")
    manifest, samples, answers = load_data()
    cases = [s for s in samples if s["split"] == split]
    rows, spent, held = [], 0, 0
    for sample in cases:
        pair = {"id": sample["id"], "group": sample["group"], "kind": sample["kind"]}
        for label, mode in [("baseline", "baseline"), ("candidate", candidate)]:
            public = {k: v for k, v in sample.items() if k not in {"split", "origin", "group"}}
            reserve = len(json.dumps(public, sort_keys=True).encode()) + 4096
            if spent + held + reserve > budget:
                result = {"status": "budget_denied", "task_pass": False, "quality_pass": False,
                          "safety_pass": False, "review_pending": False, "reason": "budget_exhausted",
                          "fixture_units": 0, "usage_state": "not_started"}
            else:
                held += reserve
                result = run_candidate(sample, answers[sample["id"]], mode, timeout=timeout)
                if result["usage_state"] == "known":
                    held -= reserve
                    spent += result["fixture_units"]
            pair[label] = result
        rows.append(pair)
    report = {"run_kind": "controlled_deterministic_fixture_no_real_model",
              "created_at": datetime.now(timezone.utc).isoformat(), "dataset": manifest,
              "split": split, "baseline_id": "baseline", "candidate_id": candidate,
              "changes": {"prompt_v2": "request_normalizer", "retrieval_v2": "status_filter_removed",
                          "model_v2": "controlled_generator_defect"}.get(candidate, candidate),
              "provenance": {"python": sys.version.split()[0], "candidate_sha256": sha((ROOT / "candidate.py").read_bytes()),
                             "pipeline_sha256": sha(Path(__file__).read_bytes()),
                             "answer_file_passed_to_candidate": False,
                             "isolation": "cooperative subprocess, not an OS sandbox"},
              "budget": {"limit_fixture_units": budget, "spent_fixture_units": spent,
                         "unknown_reservations": held,
                         "unit": "public task JSON bytes plus candidate response JSON bytes; not model tokens or money"},
              "rows": rows, "statistics": paired_statistics(rows, seed)}
    report["gate"] = release_gate(report)
    report["failures"] = [{"id": r["id"], "kind": r["kind"], "baseline_reason": r["baseline"]["reason"],
                           "candidate_reason": r["candidate"]["reason"]}
                          for r in rows if not r["candidate"]["task_pass"] or not r["candidate"]["quality_pass"]]
    return report


def calibration():
    # Execute both graders on authored counterexamples. Labels describe these
    # mechanically inspectable examples, not a human rater agreement study.
    _, samples, answers = load_data()
    file = next(s for s in samples if s["split"] == "dev" and s["kind"] == "file")
    answer = next(s for s in samples if s["split"] == "dev" and s["kind"] == "answer")
    ft, at = answers[file["id"]], answers[answer["id"]]
    good = {"service.cfg": ft["expected_file"], "policy.lock": ft["protected"]}
    unchanged = file["files"]
    supported = {"message": f"The window is {at['days']} days.", "days": at["days"], "citations": at["supporting_ids"]}
    examples = [("file-written", file, {"message": "done"}, good, True),
        ("claims-done-file-unchanged", file, {"message": "done"}, unchanged, False),
        ("correct-value-wrong-citation", answer, {**supported, "citations": ["wrong-doc"]}, {}, False),
        ("empty-answer", answer, {**supported, "message": ""}, {}, False),
        ("supported-answer", answer, supported, {}, True),
        ("explicit-failure", file, {"message": "failed"}, unchanged, False)]
    matrices = {name: {"tp": 0, "fp": 0, "tn": 0, "fn": 0} for name in ["naive", "contract"]}
    cases = []
    for sid, sample, response, artifacts, reference in examples:
        truth = answers[sample["id"]]
        naive_pass = ("done" in response["message"] if sample["kind"] == "file"
                      else str(truth["days"]) in response["message"])
        actual = score(sample, truth, response, artifacts)
        contract_pass = all(actual[k] for k in ["task_pass", "quality_pass", "safety_pass"])
        for name, predicted in [("naive", naive_pass), ("contract", contract_pass)]:
            matrices[name][("t" if predicted == reference else "f") + ("p" if predicted else "n")] += 1
        cases.append({"id": sid, "naive_pass": naive_pass, "contract_pass": contract_pass,
                      "reference_pass": reference, "score_detail": actual})
    return {"kind": "authored_counterexamples_not_human_or_model_judge_measurements",
            "confusion": matrices,
            "naive_false_positive_rate": matrices["naive"]["fp"] / (matrices["naive"]["fp"] + matrices["naive"]["tn"]),
            "cases": cases}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=sorted(MODES), default="prompt_v2")
    parser.add_argument("--split", choices=["train", "dev", "acceptance"], default="acceptance")
    parser.add_argument("--budget", type=int, default=2_000_000)
    parser.add_argument("--output", type=Path, default=Path("lab/evidence/report.json"))
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    report = compare(args.candidate, args.split, args.budget)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"candidate": args.candidate, "cases": len(report["rows"]),
                      "statistics": report["statistics"], "gate": report["gate"],
                      "failures": report["failures"], "output": str(args.output)}, ensure_ascii=False))
    if args.require_pass and not report["gate"]["passed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
