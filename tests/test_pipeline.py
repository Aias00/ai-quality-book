import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lab.pipeline import ROOT, calibration, compare, load_data, paired_statistics, run_candidate, score, sha
from lab.review import apply


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.samples, cls.answers = load_data()
        cls.good = compare("prompt_v2")
        cls.bad = compare("model_v2")

    def test_dataset_fingerprints_and_group_isolation(self):
        self.assertEqual(self.manifest["splits"]["acceptance"], {"samples": 12, "groups": 6})
        groups = {s: {r["group"] for r in self.samples if r["split"] == s} for s in ["train", "dev", "acceptance"]}
        self.assertFalse(groups["train"] & groups["dev"])
        self.assertFalse(groups["dev"] & groups["acceptance"])

    def test_candidate_workdir_has_no_reference_answers_or_grader(self):
        for row in self.good["rows"]:
            for side in [row["baseline"], row["candidate"]]:
                visible = side["candidate_visible_files"]
                self.assertNotIn("answers.json", visible)
                self.assertNotIn("pipeline.py", visible)
                self.assertIn("candidate.py", visible)
                self.assertIn("task.json", visible)
        self.assertEqual(self.good["provenance"]["isolation"], "cooperative subprocess, not an OS sandbox")

    def test_claimed_completion_does_not_override_file_evidence(self):
        failed = [r for r in self.bad["rows"] if r["kind"] == "file"]
        self.assertTrue(all(r["candidate"]["response"]["message"] == "done" for r in failed))
        self.assertTrue(all(not r["candidate"]["task_pass"] for r in failed))
        self.assertTrue(all(r["candidate"]["quality_pass"] for r in failed))

    def test_citation_identity_is_separate_from_correct_value(self):
        rows = [r for r in self.bad["rows"] if r["kind"] == "answer"]
        self.assertTrue(all(r["candidate"]["quality_pass"] for r in rows))
        self.assertTrue(all(not r["candidate"]["task_pass"] for r in rows))

    def test_controlled_request_fix_passes_fixture_gate(self):
        self.assertTrue(self.good["gate"]["passed"])
        self.assertEqual(self.good["statistics"]["difference"], 0.25)
        self.assertEqual(self.good["statistics"]["paired_groups"], 6)

    def test_generator_defect_fails_gate_and_keeps_case_failures(self):
        self.assertFalse(self.bad["gate"]["passed"])
        self.assertIn("new_task_regression", self.bad["gate"]["reasons"])
        self.assertEqual(len(self.bad["failures"]), 12)

    def test_retrieval_change_attribution_is_recorded(self):
        result = compare("retrieval_v2")
        self.assertEqual(result["changes"], "status_filter_removed")
        self.assertEqual(result["statistics"]["difference"], -0.5)
        self.assertEqual(sum(r["kind"] == "answer" for r in result["failures"]), 6)

    def test_budget_denials_remain_in_denominator_and_gate(self):
        report = compare("prompt_v2", budget=1)
        self.assertEqual(len(report["rows"]), 12)
        self.assertEqual(report["budget"]["spent_fixture_units"], 0)
        self.assertFalse(report["gate"]["passed"])
        self.assertIn("incomplete_or_unscored_pairs", report["gate"]["reasons"])

    def test_timeout_keeps_unknown_reservation(self):
        sample = self.samples[0]
        result = run_candidate(sample, self.answers[sample["id"]], "timeout", timeout=0.05)
        self.assertEqual((result["reason"], result["usage_state"]), ("timeout", "unknown"))
        report = compare("timeout", budget=15000, timeout=0.04)
        self.assertGreater(report["budget"]["unknown_reservations"], 0)
        self.assertFalse(report["gate"]["passed"])

    def test_task_success_and_presentation_quality_can_diverge(self):
        sample = next(s for s in self.samples if s["kind"] == "answer")
        result = run_candidate(sample, self.answers[sample["id"]], "terse")
        self.assertTrue(result["task_pass"])
        self.assertFalse(result["quality_pass"])

    def test_protected_artifact_change_is_independent_safety_failure(self):
        sample = next(s for s in self.samples if s["kind"] == "file")
        result = run_candidate(sample, self.answers[sample["id"]], "unsafe")
        self.assertFalse(result["safety_pass"])

    def test_calibration_executes_both_graders_and_finds_false_positives(self):
        result = calibration()
        self.assertEqual(result["confusion"]["naive"], {"tp": 2, "fp": 2, "tn": 2, "fn": 0})
        self.assertEqual(result["confusion"]["contract"], {"tp": 2, "fp": 0, "tn": 4, "fn": 0})
        self.assertEqual(result["naive_false_positive_rate"], 0.5)

    def test_bootstrap_preserves_pair_and_project_unit(self):
        rows = copy.deepcopy(self.good["rows"])
        result = paired_statistics(rows, seed=22)
        self.assertEqual(result, paired_statistics(list(reversed(rows)), seed=22))
        self.assertEqual(result["paired_groups"], 6)
        self.assertLessEqual(result["percentile_interval_95"][0], result["difference"])
        self.assertGreaterEqual(result["percentile_interval_95"][1], result["difference"])

    def test_development_split_cannot_be_published_by_gate(self):
        result = compare("prompt_v2", split="dev")
        self.assertIn("not_acceptance_split", result["gate"]["reasons"])

    def test_pending_review_blocks_release_and_wrong_report_is_rejected(self):
        report = compare("review")
        self.assertIn("unresolved_review", report["gate"]["reasons"])
        raw = json.dumps(report).encode()
        decisions = {"report_sha256": "wrong", "decisions": []}
        with self.assertRaises(ValueError):
            apply(report, raw, decisions)
        with self.assertRaises(ValueError):
            apply({**report, "candidate_id": "different"}, raw,
                  {"report_sha256": sha(raw), "decisions": []})

    def test_review_cannot_erase_artifact_failure(self):
        report = compare("review")
        raw = json.dumps(report).encode()
        decisions = {"report_sha256": sha(raw), "decisions": [{"sample_id": r["id"],
            "decision": "accept_presentation", "reviewer": "teaching-reviewer",
            "rationale": "Authored workflow demonstration, not authenticated human judgment"}
            for r in report["rows"]]}
        reviewed = apply(report, raw, decisions)
        self.assertNotIn("unresolved_review", reviewed["gate"]["reasons"])
        self.assertEqual([r["candidate"]["task_pass"] for r in report["rows"]],
                         [r["candidate"]["task_pass"] for r in reviewed["rows"]])

    def test_cli_returns_nonzero_for_blocked_release(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.run([sys.executable, "-m", "lab.pipeline", "--candidate", "retrieval_v2",
                "--require-pass", "--output", str(Path(directory)/"report.json")],
                cwd=ROOT.parent, capture_output=True, text=True)
            self.assertEqual(process.returncode, 2)
            self.assertFalse(json.loads((Path(directory)/"report.json").read_text())["gate"]["passed"])


if __name__ == "__main__":
    unittest.main()
