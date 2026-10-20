# Prediction commitments and outcome scoring (experimental)

A commit-before-evaluate discipline helps distinguish frozen pre-outcome predictions from edited predictions. The API is intentionally small and independent of any particular agent framework.

```python
from dataclasses import asdict
from humility.core import Prediction
from humility.experiment import commit_predictions, score_committed

predictions = (Prediction("case-1", 0.8, True, "source-1"),)
commitment = commit_predictions("trial-001", predictions)
# Persist asdict(commitment) with an independently held trial record BEFORE
# the label custodian releases outcomes. This library does not prove the timing.
print(asdict(commitment))
# Later: separate evaluator supplies actual labels.
report = score_committed(commitment, predictions, {"case-1": True})
print(report)
```

The SHA-256 digest binds the challenge identifier and a deterministic, case-ID-sorted representation of all prediction values and evidence identifiers. Changed probabilities, answers, evidence IDs, challenge identity or case membership fail comparison. Reordering the same cases does not alter commitment identity. The evaluator must provide a complete set of boolean outcomes, and the report retains abstention costs and Brier score.

**Threat model and limitations.** Anyone controlling both the precommitment and outcomes can regenerate matching hashes. The digest does not attest when either was written, authenticate evidence or outcome labels, prove hidden evaluator custody, or guard against answer-key leakage. For independent evaluation, a separate authority must freeze the commitment *before* revealing labels, record custody, and observe the actual candidate/evaluator isolation. Small binary outcome digests are not secret: exhaustive guesses are possible, so do not mistake hashes for encryption.

The API intentionally returns `independent_evaluator_verified=False` and `pre_outcome_timing_verified=False`, even on a passing toy fixture. No deployment or behavioral-learning qualification results from this test.
