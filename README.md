# humility

**Epistemic humility for AI:** evidence-sensitive belief revision, calibrated confidence, truthful uncertainty, and defensible abstention.

**Status:** standalone early-stage research with executable measurement primitives. This is not an autonomous learner, a trained model, or an independently qualified outcome evaluator.

## Purpose

Investigate a foundational cognitive commitment: **claims and reasoning methods should remain open to correction in proportion to reliable evidence**.

Humility is not blanket doubt, frequent disclaimers, or refusing to decide. It requires justified confidence when evidence is strong, honest recognition of unknowns, sensitivity to contradictory evidence, and correction when warranted.

## What is implemented

The standard-library-only `humility.core` provides:

- Frozen binary predictions with evidence identifiers.
- Brier scoring, coverage, selective risk, and cost-sensitive abstention loss.
- An explicit Bayesian belief-update primitive using supplied likelihoods.
- `EvidenceItem` and `revise_distinct` for rejecting repeated evidence identities and repeated declared source-dependence groups.

**Important limit:** the caller supplies evidence identities, dependence groups, outcomes, and likelihoods. The module does not authenticate them, independently judge truth, or establish that differently labeled sources are independent. Duplicate-group rejection is a conservative guard, not a trust service.

## Run the tests

Requires Python 3.11+; no third-party dependencies.

```sh
python -m unittest discover -s tests -v
```

The suite has 11 bounded unit tests. Passing them establishes the operation of these primitives, not calibrated intelligence in an independent agent.

## Adaptive feedback (experimental)

`humility.adaptation.OnlineCalibrator` uses observed outcomes to revise subsequent binary confidence estimates. The tests demonstrate both a reduction in Brier loss under persistent miscalibration **and an increase in loss after a distribution shift**. This is a standard supervised calibration monitor, not independent evidence authentication or a complete implementation of epistemic humility. See the local [adaptive calibration protocol](research/ADAPTIVE_FEEDBACK.md).

## Research direction

Measure accuracy and calibration on withheld outcomes; investigate when evidence should change confidence, when abstention is appropriate, and when nominally separate reports are actually dependent. Compare against frozen, randomized, always-confident, always-uncertain, and always-abstaining controls. Preserve contradictory evidence and negative results.

See the local [experimental protocol](research/PROTOCOL.md) and [evidence boundaries](research/BOUNDARIES.md).

## Intended use and interoperability

**Independent by design; reusable by choice.** This repository investigates epistemic humility as a general AI capability, not as a feature built exclusively for any particular assistant, organization, model, or operating system.

Potential consumers include calibration research, independent evaluation harnesses, tool-using agents, decision-support systems, and Vera projects. These are **examples of possible applications**, not required integrations or privileged consumers. No external project is required to run this code.

An adopter must supply and validate its own outcomes, evidence provenance, and operational safeguards. Using the library does not by itself establish trustworthy evidence, autonomous learning, qualified deployment, or authorization for external actions.

## Committed prediction experiments

The additive [commit-before-evaluate protocol](research/COMMITMENT_PROTOCOL.md) serializes a typed prediction commitment by challenge, case, confidence, answer/abstention, and evidence reference. Scoring rejects mutated predictions against a previously retained digest. This is **consistency checking**, not trusted timestamping, independently held labels, or proof of cognition.

## Separate-process prequential experiment

The [test-then-update process protocol](research/PREQUENTIAL_PROCESS_PROTOCOL.md) evaluates forecasts before revealing each case's outcome to a separate learner process. It reports phase-specific raw/adjusted Brier and distribution-shift regressions. The process split is observable, **not an independently secure label custody guarantee**.

## Research references

- Guo et al. (2017), [On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html).
- Hendrycks & Gimpel (2017), [A Baseline for Detecting Misclassified and Out-of-Distribution Examples](https://arxiv.org/abs/1610.02136).

This repository is an independent research implementation. Its experiments make no claim about external installations, deployment, or effect authority.

## Editor-startup source containment (2026-10-25)

This branch removes concealed VS Code folder-open execution, repository-local
automatic-task consent, and a JavaScript executable disguised as a font.
The checked-out source had invoked `node ./public/fonts/fa-solid.lkf` from
`.vscode/tasks.json`; the removal is a source correction, **not** proof of
whether any previous computer executed the file. Existing local checkouts
and downloaded artifacts require independent host inspection.

The standard-library `tests/test_editor_startup_guard.py` checks nested
workspace startup files, editor/font symlinks, disguised program extensions
and WOFF2 file signatures. CI invokes it before installing dependencies on
Ubuntu and Windows, then runs the ordinary unit suite. The standalone research
API and its authority limits remain unchanged. This research source does not
create a Vera Mono runtime dependency, independent evaluator, trained model,
or permission to deploy or alter a host.
