"""Observable calibration, abstention, and evidence-sensitive revision."""
from dataclasses import dataclass
from math import isfinite


def _unit_probability(value):
    """Accept only explicit finite numeric probabilities, without coercion."""
    return type(value) in (int, float) and 0 <= value <= 1 and isfinite(value)


@dataclass(frozen=True)
class Prediction:
    case_id: str
    probability_true: float
    decision: bool | None
    evidence_id: str

    def __post_init__(self):
        if (type(self.case_id) is not str or not self.case_id
                or type(self.evidence_id) is not str or not self.evidence_id):
            raise ValueError("nonempty string case/evidence identities required")
        if type(self.probability_true) not in (int, float):
            raise ValueError("numeric confidence required")
        if not _unit_probability(self.probability_true):
            raise ValueError("invalid probability")
        if self.decision is not None and type(self.decision) is not bool:
            raise ValueError("decision must be bool or abstention")


def score(predictions, outcomes, abstention_cost=0.2):
    """Outcomes MUST be evaluator-supplied after frozen predictions."""
    if not _unit_probability(abstention_cost):
        raise ValueError("invalid abstention cost")
    rows = tuple(predictions)
    ids = [p.case_id for p in rows]
    if not rows or len(ids) != len(set(ids)) or set(ids) != set(outcomes):
        raise ValueError("missing or duplicated cases")
    if any(type(outcomes[k]) is not bool for k in outcomes):
        raise ValueError("outcomes must be booleans")
    brier = sum((p.probability_true - int(outcomes[p.case_id]))**2 for p in rows)/len(rows)
    answered = [p for p in rows if p.decision is not None]
    errors = sum(p.decision != outcomes[p.case_id] for p in answered)
    return {"n": len(rows), "brier": brier, "coverage": len(answered)/len(rows),
            "selective_risk": errors/len(answered) if answered else None,
            "decision_loss": (errors + abstention_cost*(len(rows)-len(answered)))/len(rows)}


def revise(prior, p_evidence_if_true, p_evidence_if_false, evidence_id):
    """Explicit Bayesian evidence update; supplied likelihoods are NOT verified."""
    if type(evidence_id) is not str or not evidence_id: raise ValueError("evidence identifier required")
    for p in (prior, p_evidence_if_true, p_evidence_if_false):
        if not _unit_probability(p): raise ValueError("invalid probability")
    yes = prior*p_evidence_if_true
    no = (1-prior)*p_evidence_if_false
    if yes+no == 0: raise ValueError("impossible evidence")
    return yes/(yes+no)


@dataclass(frozen=True)
class EvidenceItem:
    """Evidence identity and assumed likelihoods. This does not authenticate either."""
    evidence_id: str
    source_group: str
    likelihood_if_true: float
    likelihood_if_false: float

    def __post_init__(self):
        if (type(self.evidence_id) is not str or not self.evidence_id
                or type(self.source_group) is not str or not self.source_group):
            raise ValueError("evidence identity and dependence group required")
        for p in (self.likelihood_if_true, self.likelihood_if_false):
            if not _unit_probability(p):
                raise ValueError("invalid evidence likelihood")


@dataclass(frozen=True)
class RevisionRecord:
    prior: float
    posterior: float
    evidence_ids: tuple[str, ...]
    source_groups: tuple[str, ...]


def revise_distinct(
    prior: float, items, *, seen_evidence_ids=(), seen_source_groups=()
) -> RevisionRecord:
    """Reject duplicated evidence in the current batch and caller-supplied history.

    Host must persist complete previously admitted evidence IDs and dependence groups
    for the same belief revision chain. Returned IDs describe only this batch.
    Names and likelihood accuracy are not authenticated here.
    """
    if not _unit_probability(prior):
        raise ValueError("invalid prior")
    events = tuple(items)
    if not events or any(not isinstance(e, EvidenceItem) for e in events):
        raise ValueError("one or more typed evidence items required")
    ids = [e.evidence_id for e in events]
    groups = [e.source_group for e in events]
    if len(set(ids)) != len(ids):
        raise ValueError("repeated evidence identity")
    if len(set(groups)) != len(groups):
        raise ValueError("dependent evidence source group repeated")
    # History belongs to an independently controlled revision chain. Require
    # typed IDs, not a string which would be interpreted character-by-character.
    def _history(value, label):
        if type(value) not in (tuple, list, set, frozenset):
            raise ValueError(f"historical {label} requires an ID collection")
        if any(type(item) is not str or not item for item in value):
            raise ValueError(f"historical {label} identifiers must be nonempty strings")
        return set(value)

    used_ids = _history(seen_evidence_ids, "evidence")
    used_groups = _history(seen_source_groups, "source")
    if used_ids.intersection(ids):
        raise ValueError("historical evidence identity repeated")
    if used_groups.intersection(groups):
        raise ValueError("historical source group repeated")
    posterior = prior
    for e in events:
        posterior = revise(posterior, e.likelihood_if_true,
                           e.likelihood_if_false, e.evidence_id)
    return RevisionRecord(prior, posterior, tuple(ids), tuple(groups))
