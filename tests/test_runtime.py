"""Behavioral controls at an optional, caller-invoked claim-output seam.

Each test catches a realistic false promotion: a source document or stale
receipt must not become proof that a system was installed or observed running.
"""

import unittest

from humility.runtime import (
    Assessment,
    Claim,
    Disposition,
    EvidenceClass,
    EvidenceOutcome,
    EvidenceReceipt,
    assess_claim,
    claim_fingerprint,
    render_checked_claim,
    revise_claim,
)


def receipt(id, claim="install", subject="repo@abc", group="host-1", *,
            kind=EvidenceClass.INSTALL, outcome=EvidenceOutcome.PASS, bound_to=None):
    default = Claim("install", "repo@abc", "UnboundVNC is installed", (EvidenceClass.INSTALL,))
    return EvidenceReceipt(id, claim, subject, group, kind, outcome,
                           claim_fingerprint(bound_to or default))


class TestRuntimeClaimAdmission(unittest.TestCase):
    def setUp(self):
        self.claim = Claim("install", "repo@abc", "UnboundVNC is installed", (EvidenceClass.INSTALL,))

    def test_source_only_cannot_qualify_install_or_render_as_fact(self):
        source = receipt("r1", kind=EvidenceClass.SOURCE_INSPECTION)
        result = assess_claim(self.claim, (source,))
        self.assertEqual(result.disposition, Disposition.UNVERIFIED)
        self.assertEqual(result.admitted_receipt_ids, ())
        self.assertIn("UNVERIFIED", render_checked_claim(self.claim, result))
        self.assertNotEqual(render_checked_claim(self.claim, result), self.claim.proposition)

    def test_matching_pass_allows_qualified_claim(self):
        result = assess_claim(self.claim, (receipt("r1"),))
        self.assertEqual(result.disposition, Disposition.SUPPORTED)
        self.assertEqual(result.admitted_receipt_ids, ("r1",))
        self.assertEqual(render_checked_claim(self.claim, result), self.claim.proposition)

    def test_stale_subject_and_other_claim_do_not_promote(self):
        for stale in (receipt("r1", subject="repo@old"), receipt("r2", claim="other")):
            with self.subTest(stale=stale.receipt_id):
                result = assess_claim(self.claim, (stale,))
                self.assertEqual(result.disposition, Disposition.UNVERIFIED)
                self.assertEqual(result.admitted_receipt_ids, ())

    def test_same_declared_group_and_repeated_id_cannot_masquerade_as_two_receipts(self):
        for rows in (
            (receipt("r1"), receipt("r2")),
            (receipt("r1"), receipt("r1", group="host-2")),
        ):
            with self.subTest(rows=rows):
                result = assess_claim(self.claim, rows)
                self.assertEqual(result.disposition, Disposition.UNVERIFIED)
                self.assertEqual(result.admitted_receipt_ids, ())

    def test_failure_overrides_pass_and_is_preserved_for_correction(self):
        positive = receipt("pass", group="build-1")
        negative = receipt("fail", group="host-2", outcome=EvidenceOutcome.FAIL)
        initial = assess_claim(self.claim, (positive,))
        updated = revise_claim(initial, self.claim, (positive, negative))
        self.assertEqual(initial.disposition, Disposition.SUPPORTED)
        self.assertEqual(updated.current.disposition, Disposition.CONTRADICTED)
        self.assertEqual(updated.previous, initial)
        self.assertIn("fail", updated.current.contradicting_receipt_ids)
        self.assertNotEqual(render_checked_claim(self.claim, updated.current), self.claim.proposition)
        self.assertTrue(updated.changed)

    def test_dependent_failure_is_visible_even_if_it_cannot_supply_independent_support(self):
        # If a source retracts its own previous PASS, duplicate-group caution
        # must not erase evidence of the retraction and leave a false PASS.
        positive = receipt("pass", group="same-report")
        negative = receipt("retraction", group="same-report", outcome=EvidenceOutcome.FAIL)
        result = assess_claim(self.claim, (positive, negative))
        self.assertEqual(result.disposition, Disposition.CONTRADICTED)
        self.assertIn("retraction", result.contradicting_receipt_ids)
        self.assertEqual(result.admitted_receipt_ids, ())

    def test_missing_evidence_is_unverified_not_supported(self):
        result = assess_claim(self.claim, ())
        self.assertEqual(result.disposition, Disposition.UNVERIFIED)

    def test_assessment_is_redacted_and_reasons_never_repeat_proposition(self):
        sensitive = Claim("claim-a", "repo@abc", "Secret token: do-not-repeat", (EvidenceClass.INSTALL,))
        result = assess_claim(sensitive, (receipt("bad", claim="claim-a", outcome=EvidenceOutcome.FAIL,
                                                  bound_to=sensitive),))
        self.assertEqual(result.disposition, Disposition.CONTRADICTED)
        self.assertNotIn(sensitive.proposition, repr(result))
        self.assertNotIn(sensitive.proposition, " ".join(result.reason_codes))

    def test_typed_records_fail_closed_on_malformed_inputs(self):
        invalid_claims = (
            ("", "repo@abc", "claim", (EvidenceClass.TEST,)),
            ("x", "", "claim", (EvidenceClass.TEST,)),
            ("x", "repo@abc", "", (EvidenceClass.TEST,)),
            ("x", "repo@abc", "claim", ()),
            ("x", "repo@abc", "claim", ("INSTALL",)),
            (True, "repo@abc", "claim", (EvidenceClass.INSTALL,)),
        )
        for args in invalid_claims:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    Claim(*args)
        for kwargs in ({"kind": "INSTALL"}, {"outcome": True}, {"group": ""}, {"claim": ""},
                       {"subject": ""}, {"id": ""}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    receipt(kwargs.get("id", "a"), kwargs.get("claim", "install"),
                            kwargs.get("subject", "repo@abc"), kwargs.get("group", "g"),
                            kind=kwargs.get("kind", EvidenceClass.TEST),
                            outcome=kwargs.get("outcome", EvidenceOutcome.PASS))

    def test_output_cannot_reuse_assessment_for_a_different_claim(self):
        valid = assess_claim(self.claim, (receipt("r1"),))
        other = Claim("install", "repo@other", "wrong computer installed", (EvidenceClass.INSTALL,))
        with self.assertRaises(ValueError):
            render_checked_claim(other, valid)

    def test_supported_assessment_cannot_transfer_to_another_proposition_or_evidence_bar(self):
        # Claim identity and subject alone are insufficient: changed semantics
        # must invalidate a previously supported assessment.
        observed = Claim("same", "repo@head", "The source file exists", (EvidenceClass.DOC,))
        evidence = receipt("doc-1", "same", "repo@head", "doc-source", kind=EvidenceClass.DOC,
                           bound_to=observed)
        supported = assess_claim(observed, (evidence,))
        for different in (
            Claim("same", "repo@head", "The host is installed and secure", (EvidenceClass.REAL_SYSTEM_PROBE,)),
            Claim("same", "repo@head", "The source file exists", (EvidenceClass.REAL_SYSTEM_PROBE,)),
            Claim("same", "repo@head", "Different source file exists", (EvidenceClass.DOC,)),
        ):
            with self.subTest(different=different):
                with self.assertRaisesRegex(ValueError, "claim"):
                    render_checked_claim(different, supported)
                with self.assertRaisesRegex(ValueError, "claim"):
                    revise_claim(supported, different, (evidence,))

    def test_evidence_receipt_for_one_proposition_cannot_support_another_with_same_id_subject(self):
        original = Claim("same", "repo@head", "Source file exists", (EvidenceClass.DOC,))
        substituted = Claim("same", "repo@head", "Host is securely running", (EvidenceClass.DOC,))
        evidence = EvidenceReceipt("receipt", "same", "repo@head", "source-1",
                                   EvidenceClass.DOC, EvidenceOutcome.PASS,
                                   claim_fingerprint(original))
        self.assertEqual(assess_claim(original, (evidence,)).disposition, Disposition.SUPPORTED)
        self.assertEqual(assess_claim(substituted, (evidence,)).disposition, Disposition.UNVERIFIED)

    def test_unverified_or_contradicted_rendering_never_repeats_the_untrusted_proposition(self):
        secret = Claim("s1", "repo@head", "Secret token: do-not-repeat", (EvidenceClass.INSTALL,))
        unknown = assess_claim(secret, ())
        failure = EvidenceReceipt("failure", "s1", "repo@head", "source", EvidenceClass.INSTALL,
                                  EvidenceOutcome.FAIL, claim_fingerprint(secret))
        contradicted = assess_claim(secret, (failure,))
        for assessment in (unknown, contradicted):
            with self.subTest(assessment=assessment.disposition):
                rendered = render_checked_claim(secret, assessment)
                self.assertIn(assessment.disposition.value, rendered)
                self.assertNotIn(secret.proposition, rendered)
                self.assertNotIn("do-not-repeat", rendered)


if __name__ == "__main__":
    unittest.main()
