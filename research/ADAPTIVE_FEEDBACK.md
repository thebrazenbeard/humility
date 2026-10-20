# Adaptive calibration: monitoring and feedback

The `OnlineCalibrator` makes a forecast **before** the label is supplied and updates a rolling calibration estimate afterward. It uses discrete probability bins, a bounded label window and shrinkage toward the base forecast. Callers may compare proper Brier scores on future cases against the unchanged original probability.

This is **online supervised recalibration**, not a model's verified introspective access, an epistemic authority, or proof of an AI learning a general law. Outcomes are untrusted caller-supplied values; labels may be duplicated, strategic, wrong or distributionally biased. In particular, improvement after repeated miscalibration can reverse after a distribution shift. The implementation emits both raw and adjusted loss so regressions remain visible.

## Experimental discipline
- Declare bin count, window size, prior strength, case order and evaluation metric before observing results.
- Make each `forecast` before `observe`; replays and simultaneous unresolved forecasts are refused.
- Compare to the original forecast, a static calibrated baseline, always-confident/uncertain and abstention strategies on future withheld cases.
- Vary the forecast base rates, dependence, OOD shifts, feedback delays and correlated/poisoned labels. A self-scored toy fixture is not independent qualification.
- A proper external evaluation needs a separate label custodian and immutable timing receipts. This package has neither.

Background: probability scoring/calibration (Guo et al., 2017, https://proceedings.mlr.press/v70/guo17a.html). No special target agent or integration is assumed.
