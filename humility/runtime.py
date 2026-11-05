"""Optional claim-evidence admission and correction for host-owned consumers.

The caller declares evidence kinds, provenance and outcomes. None are verified
or authenticated by this library, and nothing here grants effect authority.
The host must invoke this seam and retain its own authenticated receipts.
"""

from dataclasses import dataclass, field
from enum import Enum
from collections import Counter
from hashlib import sha256
from json import dumps


class EvidenceClass(str, Enum):
    DOC = "DOC"
    DEP_METADATA = "DEP_METADATA"
    SOURCE_INSPECTION = "SOURCE_INSPECTION"
    TEST = "TEST"
    BUILD = "BUILD"
    INSTALL = "INSTALL"
    REAL_SYSTEM_PROBE = "REAL_SYSTEM_PROBE"
    FORMAL_VERIFY = "FORMAL_VERIFY"


class EvidenceOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class Disposition(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"


def _nonempty(value):
    return type(value) is str and bool(value.strip())


@dataclass(frozen=True)
class Claim:
    claim_id: str
    subject_ref: str
    proposition: str = field(repr=False)
    required_classes: tuple[EvidenceClass, ...]

    def __post_init__(self):
        if not all(_nonempty(v) for v in (self.claim_id, self.subject_ref, self.proposition)):
            raise ValueError("nonempty string claim identity, subject and proposition required")
        if (type(self.required_classes) is not tuple or not self.required_classes
                or any(type(v) is not EvidenceClass for v in self.required_classes)
                or len(set(self.required_classes)) != len(self.required_classes)):
            raise ValueError("distinct typed required evidence classes required")


@dataclass(frozen=True)
class EvidenceReceipt:
    receipt_id: str
    claim_id: str
    subject_ref: str
    source_group: str
    kind: EvidenceClass
    outcome: EvidenceOutcome
    claim_digest: str

    def __post_init__(self):
        if not all(_nonempty(v) for v in (
                self.receipt_id, self.claim_id, self.subject_ref, self.source_group)):
            raise ValueError("nonempty string receipt identities and source group required")
        if type(self.kind) is not EvidenceClass or type(self.outcome) is not EvidenceOutcome:
            raise ValueError("typed evidence class and outcome required")
        if (type(self.claim_digest) is not str or len(self.claim_digest) != 64
                or any(c not in "0123456789abcdef" for c in self.claim_digest)):
            raise ValueError("canonical full-claim fingerprint required")


@dataclass(frozen=True)
class Assessment:
    claim_id: str
    subject_ref: str
    claim_digest: str
    disposition: Disposition
    admitted_receipt_ids: tuple[str, ...]
    contradicting_receipt_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class Correction:
    previous: Assessment
    current: Assessment
    changed: bool


def _claim_snapshot(claim: Claim) -> Claim:
    """Revalidate fields even if a caller has mutated a frozen instance."""
    if not isinstance(claim, Claim):
        raise ValueError("typed claim required")
    return Claim(claim.claim_id, claim.subject_ref, claim.proposition, claim.required_classes)


def _claim_digest(claim: Claim) -> str:
    """Bind identity, exact subject, proposition and required evidence classes."""
    normalized = dumps((claim.claim_id, claim.subject_ref, claim.proposition,
                        sorted(e.value for e in claim.required_classes)),
                       separators=(",", ":"), ensure_ascii=False)
    return sha256(normalized.encode("utf-8")).hexdigest()


def claim_fingerprint(claim: Claim) -> str:
    """Deterministic semantic binding; not source authentication or custody."""
    return _claim_digest(_claim_snapshot(claim))


def assess_claim(claim: Claim, receipts) -> Assessment:
    """Classify caller-asserted evidence for this exact claim and subject.

    Matching duplicate IDs or declared dependent source groups are removed
    entirely; they cannot be used as independent support. Contradictions from
    remaining matching evidence override positive receipts for required kinds.
    This is NOT an authorization, trust or external truth verification service.
    """
    # Copy base records once: privileged callers can mutate frozen instances.
    c = _claim_snapshot(claim)
    rows = tuple(receipts)
    if any(not isinstance(r, EvidenceReceipt) for r in rows):
        raise ValueError("typed evidence receipts required")
    rows = tuple(EvidenceReceipt(r.receipt_id, r.claim_id, r.subject_ref,
                                 r.source_group, r.kind, r.outcome,
                                 r.claim_digest) for r in rows)
    fingerprint = _claim_digest(c)
    matching = tuple(r for r in rows if r.claim_id == c.claim_id
                     and r.subject_ref == c.subject_ref
                     and r.claim_digest == fingerprint)
    ids = Counter(r.receipt_id for r in matching)
    groups = Counter(r.source_group for r in matching)
    eligible = tuple(r for r in matching
                     if ids[r.receipt_id] == 1 and groups[r.source_group] == 1
                     and r.kind in c.required_classes)
    positive = tuple(r.receipt_id for r in eligible if r.outcome is EvidenceOutcome.PASS)
    # A retraction or contradiction from the same declared source is not a
    # second independent confirmation, but must remain visible and block an
    # unqualified positive assertion. None of these IDs prove authenticity.
    negative = tuple(dict.fromkeys(r.receipt_id for r in matching
                                  if r.kind in c.required_classes
                                  and r.outcome is EvidenceOutcome.FAIL))
    reasons = []
    if len(matching) != len(rows):
        reasons.append("SCOPE_MISMATCH_IGNORED")
    if any(n > 1 for n in ids.values()) or any(n > 1 for n in groups.values()):
        reasons.append("DUPLICATED_OR_DEPENDENT_EVIDENCE_IGNORED")
    if negative:
        disposition = Disposition.CONTRADICTED
        reasons.append("MATCHING_FAILURE_OBSERVED")
    elif set(c.required_classes).issubset(
            {r.kind for r in eligible if r.outcome is EvidenceOutcome.PASS}):
        disposition = Disposition.SUPPORTED
        reasons.append("REQUIRED_CLASSES_PRESENT")
    else:
        disposition = Disposition.UNVERIFIED
        reasons.append("REQUIRED_CLASSES_UNVERIFIED")
    return Assessment(c.claim_id, c.subject_ref, _claim_digest(c), disposition,
                      positive, negative, tuple(reasons))


def revise_claim(previous: Assessment, claim: Claim, receipts) -> Correction:
    """Compare a prior admission with new total evidence; retain both states.

    Caller supplies the complete retained evidence history for re-evaluation.
    The prior state never substitutes for a missing or unverifiable receipt.
    """
    if not isinstance(previous, Assessment):
        raise ValueError("typed prior assessment and claim required")
    c = _claim_snapshot(claim)
    if (previous.claim_id != c.claim_id or previous.subject_ref != c.subject_ref
            or previous.claim_digest != _claim_digest(c)):
        raise ValueError("prior assessment does not match exact claim subject")
    current = assess_claim(c, receipts)
    return Correction(previous, current, previous.disposition != current.disposition)


def render_checked_claim(claim: Claim, assessment: Assessment) -> str:
    """Optional observable output seam for an explicitly submitted claim.

    It does not capture claims omitted by a model or prove assessment origin.
    A host-owned dispatcher must enforce usage and evidence provenance.
    """
    if not isinstance(assessment, Assessment):
        raise ValueError("typed claim and assessment required")
    c = _claim_snapshot(claim)
    if (assessment.claim_id != c.claim_id or assessment.subject_ref != c.subject_ref
            or assessment.claim_digest != _claim_digest(c)):
        raise ValueError("assessment does not match exact claim subject")
    if type(assessment.disposition) is not Disposition:
        raise ValueError("typed assessment disposition required")
    if assessment.disposition is Disposition.SUPPORTED:
        return c.proposition
    if assessment.disposition is Disposition.UNVERIFIED:
        return "UNVERIFIED — claim evidence is insufficient"
    return "CONTRADICTED — conflicting evidence was reported"
