"""Deterministic prediction commitments for later scoring, not a trusted timestamp.

This module checks consistency of supplied data. A digest alone cannot
establish independent evaluator custody or that a commitment predates labels.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from .core import Prediction, score

SCHEMA = 'HUMILITY_PREDICTION_COMMITMENT_V1'


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _hash(value):
    return sha256(_canonical(value)).hexdigest()


def _prediction_rows(predictions):
    predictions = tuple(predictions)
    if not predictions or any(not isinstance(p, Prediction) for p in predictions):
        raise ValueError('nonempty typed predictions required')
    for p in predictions:
        if type(p.case_id) is not str or not p.case_id or type(p.evidence_id) is not str or not p.evidence_id:
            raise ValueError('nonempty string identifiers required')
        if type(p.probability_true) not in (int, float) or type(p.probability_true) is bool:
            raise ValueError('numeric confidence required')
    ids = [p.case_id for p in predictions]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate case identity')
    return [asdict(p) for p in sorted(predictions, key=lambda p: p.case_id)]


@dataclass(frozen=True)
class PredictionCommitment:
    schema: str
    challenge_id: str
    digest: str
    count: int


def commit_predictions(challenge_id, predictions):
    if type(challenge_id) is not str or not challenge_id:
        raise ValueError('nonempty challenge identifier required')
    rows = _prediction_rows(predictions)
    return PredictionCommitment(SCHEMA, challenge_id,
                                _hash({'schema': SCHEMA, 'challenge_id': challenge_id, 'rows': rows}),
                                len(rows))


def score_committed(commitment, predictions, outcomes, *, abstention_cost=0.2):
    """Check an externally retained commitment before scoring externally given labels."""
    if not isinstance(commitment, PredictionCommitment) or commitment.schema != SCHEMA:
        raise ValueError('invalid commitment schema')
    predictions = tuple(predictions)  # permit one-shot prediction iterables
    _prediction_rows(predictions)
    expected = commit_predictions(commitment.challenge_id, predictions)
    if commitment != expected:
        raise ValueError('prediction commitment mismatch')
    if not isinstance(outcomes, dict) or any(type(k) is not str for k in outcomes):
        raise ValueError('outcomes must map case IDs to booleans')
    metrics = score(predictions, outcomes, abstention_cost=abstention_cost)
    return {'schema': 'HUMILITY_SCORING_RECEIPT_V1',
            'challenge_id': commitment.challenge_id,
            'prediction_digest': commitment.digest,
            'outcome_digest': _hash(outcomes),
            'metrics': metrics,
            'independent_evaluator_verified': False,
            'pre_outcome_timing_verified': False,
            'evidence_authenticity_verified': False}
