# humility

**Epistemic humility for AI:** evidence-sensitive belief revision, calibrated confidence, truthful uncertainty and defensible abstention.

**Status:** early research with executable measurement primitives. This is not an autonomous learner, trained model, independent outcome evaluator, or deployed Vera runtime.

`humility.core` provides frozen predictions and evidence IDs, binary Brier scoring, selective risk, coverage, cost-sensitive decision loss, an explicit Bayesian revision primitive, and a conservative provenance-aware update that rejects repeated evidence identities and repeated source-dependence groups. It does not authenticate evidence sources or judge the truth of supplied likelihoods. Outcomes must be controlled by a separate evaluator for meaningful independent evidence.

Run `python -m unittest discover -s tests -v` (Python 3.11+). The suite currently contains **11 bounded tests**, not independent model qualification.

The proposed foundational law is that *claims and cognitive methods remain open to revision in proportion to reliable contradictory evidence*. This does not imply permanent doubt or reflexive abstention. Measurable humility means justified confidence, correction when indicated, resistance to contaminated evidence, and accountable claims.

The additional `EvidenceItem` / `revise_distinct` interface refuses to count two reports from the same declared dependency group as independent updates. **The caller supplies those groups and likelihoods**—this prevents some accidental double-counting but does not establish authenticity, independence, or accurate Bayesian likelihoods. It is not a trust service.

See [research/PROTOCOL.md](research/PROTOCOL.md) for competing controls, falsification, and qualification boundaries. Related but independent: [meta](https://github.com/thebrazenbeard/meta), which studies improved **methods of inquiry**, not just confidence in outcomes. [Vera Mono PR #74](https://github.com/thebrazenbeard/vera-mono/pull/74) proposes endogenous learning studies; its existence does not establish such capability.

Research influences: [Guo et al. (2017)](https://proceedings.mlr.press/v70/guo17a.html) on calibration and [Hendrycks & Gimpel (2017)](https://arxiv.org/abs/1610.02136) on error/OOD detection.
