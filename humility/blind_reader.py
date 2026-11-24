"""Explicit, model-neutral blind-reader audit for interpretation drift.

A caller supplies the alternate readings. This code checks provenance and
modality preservation; it cannot discover interpretations, verify their
plausibility, read hidden intentions, or authorize an action.
"""
from dataclasses import dataclass

MODALITIES = frozenset({
    'DESCRIPTION', 'ASSERTION', 'QUESTION', 'HYPOTHETICAL',
    'ABSTRACT_CONSIDERATION', 'DESIRE', 'INTENTION',
    'PREPARED_ACTION', 'REPORTED_ACTION', 'REQUEST', 'CORRECTION',
    'UNCERTAIN',
})


def _text(value, label):
    if type(value) is not str or not value.strip():
        raise ValueError(f'{label} must be nonblank text')
    return value


def _text_tuple(value, label, *, allow_empty=False):
    if type(value) not in (list, tuple):
        raise ValueError(f'{label} must be a list or tuple of nonblank strings')
    result = tuple(_text(item, label) for item in value)
    if not result and not allow_empty:
        raise ValueError(f'{label} cannot be empty')
    if len(result) > 12:
        raise ValueError(f'{label} exceeds maximum entries')
    return result


@dataclass(frozen=True)
class CandidateReading:
    """Caller-proposed reading; quotes are verifiable, interpretation is not."""
    reading_id: str
    paraphrase: str
    quoted_evidence: tuple[str, ...]
    modality: str
    unstated_assumptions: tuple[str, ...] = ()

    def __post_init__(self):
        _text(self.reading_id, 'reading_id')
        _text(self.paraphrase, 'paraphrase')
        _text_tuple(self.quoted_evidence, 'quoted_evidence')
        _text_tuple(self.unstated_assumptions, 'unstated_assumptions', allow_empty=True)
        if self.modality not in MODALITIES or type(self.modality) is not str:
            raise ValueError('unknown modality')


@dataclass(frozen=True)
class BlindReaderResult:
    status: str
    alternative_reading_ids: tuple[str, ...]
    modality_mismatches: tuple[str, ...]
    uncertain_assumptions: tuple[str, ...]
    unverified_plausibility: bool = True
    action_effect: str = 'NONE'


def review(utterance: str, declared_modality: str, candidates) -> BlindReaderResult:
    """Surface competing grounded *proposals*, not inferred facts.

    declared_modality is caller-supplied and NOT detected by this function.
    Exact quote matches are provenance checks, NOT proof of correct reading.
    """
    _text(utterance, 'utterance')
    if len(utterance) > 32768:
        raise ValueError('utterance too long')
    if type(declared_modality) is not str or declared_modality not in MODALITIES:
        raise ValueError('invalid declared modality')
    proposed = tuple(candidates)
    if not (1 <= len(proposed) <= 8):
        raise ValueError('1 to 8 candidate readings required')
    if any(not isinstance(c, CandidateReading) for c in proposed):
        raise ValueError('typed candidate readings required')
    # Revalidate caller-mutable instances and snapshot the exact values used.
    rows = tuple(CandidateReading(c.reading_id, c.paraphrase,
                                   tuple(c.quoted_evidence), c.modality,
                                   tuple(c.unstated_assumptions)) for c in proposed)
    ids = tuple(c.reading_id for c in rows)
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate reading_id')
    for reading in rows:
        for quote in reading.quoted_evidence:
            if quote not in utterance:
                raise ValueError(f'quoted evidence not found in source for {reading.reading_id}')
    mismatch = tuple(c.reading_id for c in rows if c.modality != declared_modality)
    assumptions = tuple(c.reading_id for c in rows if c.unstated_assumptions)
    alternatives = ids if len({c.paraphrase for c in rows}) > 1 else ()
    status = ('REVIEW_REQUIRED' if alternatives or mismatch or assumptions
              else 'NO_CONFLICT_OBSERVED')
    return BlindReaderResult(status, alternatives, mismatch, assumptions)
