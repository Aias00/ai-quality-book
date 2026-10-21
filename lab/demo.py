"""Run three controlled comparisons and calibration; verify expected gate results."""
import argparse
import json
from pathlib import Path
from .pipeline import calibration, compare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("lab/evidence"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    summary = {"kind": "controlled_fixture_no_real_models", "reports": [], "calibration": calibration()}
    for name in ["prompt_v2", "retrieval_v2", "model_v2"]:
        report = compare(name)
        assert report["gate"]["passed"] == (name == "prompt_v2")
        path = args.output / (name + ".json")
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        summary["reports"].append({"candidate": name, "cases": len(report["rows"]),
            "statistics": report["statistics"], "gate": report["gate"],
            "failure_count": len(report["failures"]), "budget": report["budget"]})
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
