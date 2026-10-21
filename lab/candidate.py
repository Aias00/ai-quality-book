"""Cooperative deterministic candidates, copied into a fresh temporary directory.

These are executable baselines and injected defects, not real LLM adapters.
No reference labels, grader or source repository path are supplied here.
"""
from pathlib import Path
import json
import re
import sys
import time


def main():
    mode = sys.argv[1]
    task = json.loads(Path("task.json").read_text())
    if mode == "timeout":
        time.sleep(5)
    if task["kind"] == "file":
        if mode == "prompt_v2":
            # A controlled request-normalization change. It does not measure
            # how a real language model responds to a different prompt.
            match = re.search(r"timeout_ms to (\d+)", task["instruction"])
        else:
            match = re.search(r"\d+", task["instruction"])
        value = int(match[0] if mode != "prompt_v2" else match[1])
        if mode != "model_v2":
            Path("service.cfg").write_text(f"timeout_ms={value}\nretries=2\n")
        if mode == "unsafe":
            Path("policy.lock").write_text("overwritten\n")
        result = {"message": "done", "needs_review": mode == "review"}
        if mode == "terse":
            result["message"] = ""
    else:
        docs = task["documents"]
        permitted = docs if mode == "retrieval_v2" else [d for d in docs if d["status"] == "current"]
        document = permitted[0]
        citations = [document["id"]]
        if mode == "model_v2":
            citations = [docs[0]["id"]]
        result = {"message": f"The refund window is {document['days']} days.",
                  "days": document["days"], "citations": citations,
                  "needs_review": mode == "review"}
        if mode == "terse":
            result["message"] = ""
    Path("response.json").write_text(json.dumps(result))


if __name__ == "__main__":
    main()
