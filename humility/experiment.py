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
    # Capture once and retain V1 serialization, including dataclass-subclass
    # fields. Revalidating from these rows rejects mutated frozen instances
    # without silently changing existing commitment digests.
    rows = tuple(asdict(p) for p in predictions)
    for row in rows:
        Prediction(row['case_id'], row['probability_true'], row['decision'], row['evidence_id'])
    ids = [row['case_id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate case identity')
    return sorted(rows, key=lambda row: row['case_id'])


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
    if not isinstance(commitment, PredictionCommitment):
        raise ValueError('invalid commitment schema')
    # Retain the exact validated commitment fields for the entire receipt.
    # Python frozen instances are still mutable through object.__setattr__.
    frozen_commitment = PredictionCommitment(commitment.schema, commitment.challenge_id,
                                             commitment.digest, commitment.count)
    if type(frozen_commitment.schema) is not str or frozen_commitment.schema != SCHEMA:
        raise ValueError('invalid commitment schema')
    if type(frozen_commitment.challenge_id) is not str or not frozen_commitment.challenge_id:
        raise ValueError('nonempty challenge identifier required')
    if (type(frozen_commitment.digest) is not str or
            type(frozen_commitment.count) is not int or frozen_commitment.count < 1):
        raise ValueError('invalid commitment digest or count')
    rows = _prediction_rows(predictions)  # also permits one-shot iterables
    expected = PredictionCommitment(SCHEMA, frozen_commitment.challenge_id,
                                    _hash({'schema': SCHEMA, 'challenge_id': frozen_commitment.challenge_id,
                                           'rows': rows}), len(rows))
    if frozen_commitment != expected:
        raise ValueError('prediction commitment mismatch')
    if not isinstance(outcomes, dict):
        raise ValueError('outcomes must map case IDs to booleans')
    # Preserve one plain mapping for both scoring and the receipt digest.
    # An arbitrary dict subclass can override __getitem__ to return values
    # different from the values json serializes for the same object.
    frozen_outcomes = dict(outcomes)
    if any(type(k) is not str for k in frozen_outcomes):
        raise ValueError('outcomes must map case IDs to booleans')
    # Score the exact core fields that were committed, not a second read of
    # potentially stateful subclass attributes.
    frozen = tuple(Prediction(row['case_id'], row['probability_true'], row['decision'], row['evidence_id'])
                   for row in rows)
    metrics = score(frozen, frozen_outcomes, abstention_cost=abstention_cost)
    return {'schema': 'HUMILITY_SCORING_RECEIPT_V1',
            'challenge_id': frozen_commitment.challenge_id,
            'prediction_digest': frozen_commitment.digest,
            'outcome_digest': _hash(frozen_outcomes),
            'metrics': metrics,
            'independent_evaluator_verified': False,
            'pre_outcome_timing_verified': False,
            'evidence_authenticity_verified': False}
