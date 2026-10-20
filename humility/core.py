"""Observable calibration, abstention, and evidence-sensitive revision."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Prediction:
    case_id: str
    probability_true: float
    decision: bool | None
    evidence_id: str

    def __post_init__(self):
        if not self.case_id or not self.evidence_id:
            raise ValueError("nonempty case/evidence identities required")
        if not isfinite(self.probability_true) or not 0 <= self.probability_true <= 1:
            raise ValueError("invalid probability")
        if self.decision is not None and type(self.decision) is not bool:
            raise ValueError("decision must be bool or abstention")


def score(predictions, outcomes, abstention_cost=0.2):
    """Outcomes MUST be evaluator-supplied after frozen predictions."""
    if not isfinite(abstention_cost) or not 0 <= abstention_cost <= 1:
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
    if not evidence_id: raise ValueError("evidence identifier required")
    for p in (prior, p_evidence_if_true, p_evidence_if_false):
        if not isfinite(p) or not 0 <= p <= 1: raise ValueError("invalid probability")
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
        if not self.evidence_id or not self.source_group:
            raise ValueError("evidence identity and dependence group required")
        for p in (self.likelihood_if_true, self.likelihood_if_false):
            if not isfinite(p) or not 0 <= p <= 1:
                raise ValueError("invalid evidence likelihood")


@dataclass(frozen=True)
class RevisionRecord:
    prior: float
    posterior: float
    evidence_ids: tuple[str, ...]
    source_groups: tuple[str, ...]


def revise_distinct(prior: float, items) -> RevisionRecord:
    """Conservative update: reject repeated/correlated groups rather than double count.

    Caller must independently verify actual source identity, likelihood accuracy,
    and true group independence. This is not an evidence-authentication API.
    """
    if not isfinite(prior) or not 0 <= prior <= 1:
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
    posterior = prior
    for e in events:
        posterior = revise(posterior, e.likelihood_if_true,
                           e.likelihood_if_false, e.evidence_id)
    return RevisionRecord(prior, posterior, tuple(ids), tuple(groups))
