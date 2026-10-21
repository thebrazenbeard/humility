"""Two-process test-then-update calibration experiment (standard library only).

Protocol withholding is observed; evaluator security/label custody is NOT qualified.
This worker and evaluator share filesystem privileges and callable source.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

from .adaptation import OnlineCalibrator


def _worker():
    learner = OnlineCalibrator()
    for line in sys.stdin:
        try:
            req = json.loads(line)
            if req.get("op") == "predict":
                rec = learner.forecast(req["case_id"], req["probability"])
                response = {"case_id": rec.case_id,
                            "raw": rec.raw_probability,
                            "adjusted": rec.adjusted_probability,
                            "prior_observations": rec.prior_observations,
                            "worker_pid": os.getpid()}
            elif req.get("op") == "feedback":
                result = learner.observe(req["case_id"], req["outcome"])
                response = {"case_id": result["case_id"], "observed": True}
            else:
                raise ValueError("unknown operation")
        except (ValueError, KeyError, TypeError) as exc:
            response = {"error": str(exc)}
        print(json.dumps(response, allow_nan=False), flush=True)


def _send(process, request):
    if process.poll() is not None:
        raise RuntimeError("learner exited unexpectedly")
    process.stdin.write(json.dumps(request, allow_nan=False) + "\n")
    process.stdin.flush()
    answer = process.stdout.readline()
    if not answer:
        raise RuntimeError("no worker response")
    response = json.loads(answer)
    if not isinstance(response, dict) or "error" in response:
        raise ValueError("worker rejected request: " + str(response))
    return response


def evaluate_stream(cases, *, feedback_overrides=None):
    """Cases (id, base_probability, boolean_label, phase) held in evaluator.

    The protocol sends each label only AFTER that case's forecast is received.
    This process distinction is not a sandbox, label secrecy or independent audit.
    """
    rows = tuple(cases)
    if not rows:
        raise ValueError("nonempty case sequence required")
    ids = [r[0] for r in rows]
    if any(len(r) != 4 for r in rows) or len(set(ids)) != len(ids):
        raise ValueError("unique four-field cases required")
    for case_id, p, outcome, phase in rows:
        if type(case_id) is not str or not case_id or type(outcome) is not bool:
            raise ValueError("invalid case identity or outcome")
        if type(phase) is not str or not phase:
            raise ValueError("nonempty phase required")
    # Cases carry the fixed evaluator-scored truth; the override simulates
    # potentially false training feedback, not another authoritative label.
    if feedback_overrides is None:
        feedback_overrides = {}
    if type(feedback_overrides) is not dict:
        raise ValueError("feedback_overrides must be an exact ID-to-bool dict")
    for case_id, feedback in feedback_overrides.items():
        if type(case_id) is not str or case_id not in ids:
            raise ValueError("feedback override references an unknown case ID")
        if type(feedback) is not bool:
            raise ValueError("feedback override requires an exact bool")
    project_root = str(Path(__file__).resolve().parents[1])
    bootstrap = ("import sys;sys.path.insert(0," + repr(project_root) +
                 ");from humility.prequential import _worker;_worker()")
    proc = subprocess.Popen([sys.executable, "-I", "-B", "-c", bootstrap],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    phases = {}
    feedback_divergent_count = 0
    try:
        for case_id, base, outcome, phase in rows:
            prediction = _send(proc, {"op": "predict", "case_id": case_id,
                                      "probability": base})
            if prediction.get("case_id") != case_id or prediction.get("worker_pid") != proc.pid:
                raise ValueError("unmatched prediction or worker")
            p = prediction["adjusted"]
            if type(p) not in (int, float) or not 0 <= p <= 1:
                raise ValueError("invalid worker forecast")
            point = phases.setdefault(phase, {"n": 0, "raw_brier": 0.0, "adjusted_brier": 0.0})
            point["n"] += 1
            point["raw_brier"] += (float(base) - int(outcome)) ** 2
            point["adjusted_brier"] += (p - int(outcome)) ** 2
            # Outcome first transmitted AFTER the forecast has been evaluated.
            feedback = feedback_overrides.get(case_id, outcome)
            feedback_divergent_count += int(feedback != outcome)
            ack = _send(proc, {"op": "feedback", "case_id": case_id,
                               "outcome": feedback})
            if ack != {"case_id": case_id, "observed": True}:
                raise ValueError("feedback acknowledgment mismatch")
        for stats in phases.values():
            stats["raw_brier"] /= stats["n"]
            stats["adjusted_brier"] /= stats["n"]
        return {"phases": phases, "worker_pid": proc.pid,
                "feedback_override_count": len(feedback_overrides),
                "feedback_divergent_count": feedback_divergent_count,
                "score_truth_origin": "EVALUATOR_LOCAL_UNAUTHENTICATED",
                "feedback_origin": "SIMULATED_UNTRUSTED",
                "separate_process_observed": proc.pid != os.getpid(),
                "prediction_before_label_protocol": True,
                "independent_label_custody_verified": False,
                "sandbox_isolation_verified": False}
    finally:
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
