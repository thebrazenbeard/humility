# Separate-process prequential calibration experiment

The evaluator retains a sequence of (case ID, base probability, boolean outcome, phase) records in its process. It starts a **distinct CPython worker process** running the existing `OnlineCalibrator`. For each case, the evaluator:

1. Sends case ID and raw probability, **not the label**, over a line-delimited JSON pipe.
2. Waits for a forecast, validates the case ID and measured worker PID, and scores both raw and adjusted probabilities **before** feedback.
3. Sends that case's outcome to the worker so it can change its future calibration estimate.
4. Reports raw and adjusted Brier scores separately for each caller-declared phase, preserving regressions on shifted data.

Run `python -m unittest discover -s tests -v` to execute the synthetic stable-and-shift checks. The API is `humility.prequential.evaluate_stream(rows)`; it requires unique IDs. Returned flags state `separate_process_observed=True`, `prediction_before_label_protocol=True`, but **`independent_label_custody_verified=False` and `sandbox_isolation_verified=False`**.

## The strongest unsolved objection

Both processes run under ordinary host permissions and share code/filesystem access. The worker could inspect source, environmental state, infer a predictable outcome rule, or exploit host permissions. The evaluator calls the worker from a trusted bundled module; its blocking line-reader is not an untrusted-code sandbox. No cryptographic commitment, authenticated label issuer, secure timestamp, hidden-key custody, or independent external reviewer is provided. If outcomes are supplied dishonestly, both results can be fabricated. A phase-specific Brier improvement on synthetic examples is NOT evidence of a self-aware or independently qualified intelligence.

The prequential pattern is intended to prevent **accidental** disclosure through prediction messages and enforce evaluation-before-update. It does not replace independent process/permission isolation or truly withheld evaluation sets. The original calibration experiment still supports ordinary library-level studies without spawning workers.

Research background: [Waghmare & Ziegel (2026), proper scoring rules](https://doi.org/10.1146/annurev-statistics-042424-050626) and [Hidalgo et al. (2019), prequential variations for concept drift](https://doi.org/10.1111/coin.12208).
