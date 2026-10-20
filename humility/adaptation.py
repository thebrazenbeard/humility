"""Online binary probability calibration from delayed outcome feedback.

Research monitor, not self-awareness, source authentication, or safe deployment.
Every outcome is caller supplied and may be false or correlated.
"""
from collections import deque
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Forecast:
    case_id: str
    raw_probability: float
    adjusted_probability: float
    prior_observations: int
    bucket: int


class OnlineCalibrator:
    """Bin-local rolling feedback with prior shrinkage; can get worse on shift."""
    def __init__(self, *, bins=10, window=20, prior_weight=4.0):
        if type(bins) is not int or bins < 2: raise ValueError("bins must be >=2")
        if type(window) is not int or window < 1: raise ValueError("window must be positive")
        if not isfinite(prior_weight) or prior_weight <= 0:
            raise ValueError("prior_weight must be positive and finite")
        self.bins = bins
        self.window = window
        self.prior_weight = prior_weight
        self._history = [deque(maxlen=window) for _ in range(bins)]
        self._pending = {}
        self._seen = set()
        self.receipts = []

    def forecast(self, case_id, probability):
        if type(case_id) is not str or not case_id or case_id in self._seen:
            raise ValueError("new nonempty case identifier required")
        if self._pending: raise ValueError("feedback required before next forecast")
        if type(probability) not in (int, float) or not isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("invalid probability")
        bucket = min(int(probability * self.bins), self.bins - 1)
        history = self._history[bucket]
        adjusted = ((self.prior_weight * probability + sum(history)) /
                    (self.prior_weight + len(history)))
        record = Forecast(case_id, float(probability), adjusted, len(history), bucket)
        self._pending[case_id] = record
        self._seen.add(case_id)
        return record

    def observe(self, case_id, outcome):
        if case_id not in self._pending:
            raise ValueError("no pending forecast for case")
        if type(outcome) is not bool: raise ValueError("boolean outcome required")
        record = self._pending.pop(case_id)
        self._history[record.bucket].append(int(outcome))
        measured = {"case_id": case_id,
                    "raw_brier": (record.raw_probability - int(outcome)) ** 2,
                    "adjusted_brier": (record.adjusted_probability - int(outcome)) ** 2,
                    "prior_observations": record.prior_observations}
        self.receipts.append(measured)
        return measured