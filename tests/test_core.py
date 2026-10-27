import unittest
from humility.core import Prediction, score, revise, EvidenceItem, revise_distinct

class TestHumility(unittest.TestCase):
    def test_calibration_and_coverage(self):
        r = score([Prediction('a', .9, True, 'e1'), Prediction('b', .4, None, 'e2')], {'a':True,'b':False})
        self.assertAlmostEqual(r['brier'], .085)
        self.assertEqual(r['coverage'], .5)
        self.assertAlmostEqual(r['decision_loss'], .1)
    def test_always_abstain_is_not_free(self):
        r = score([Prediction('a', .5, None, 'e')], {'a':True})
        self.assertEqual(r['coverage'], 0)
        self.assertIsNone(r['selective_risk'])
        self.assertGreater(r['decision_loss'], 0)
    def test_invalid_probabilities(self):
        for x in (float('nan'), float('inf'), -1, 1.1):
            with self.assertRaises(ValueError): Prediction('a', x, True, 'e')
    def test_duplicates_and_missing(self):
        p = Prediction('a', .5, True, 'e')
        with self.assertRaises(ValueError): score([p,p], {'a': True})
        with self.assertRaises(ValueError): score([p], {'b': True})
    def test_revisions_can_reverse_confidence(self):
        self.assertAlmostEqual(revise(.5, .9, .1, 'e1'), .9)
        self.assertAlmostEqual(revise(.9, .1, .9, 'e2'), .5)
    def test_impossible_evidence(self):
        with self.assertRaises(ValueError): revise(.5,0,0,'e')
    def test_distinct_sources_update_with_provenance(self):
        result = revise_distinct(.5, [EvidenceItem("a", "source-A", .9, .1),
                                        EvidenceItem("b", "source-B", .1, .9)])
        self.assertAlmostEqual(result.posterior, .5)
        self.assertEqual(result.evidence_ids, ("a", "b"))
        self.assertEqual(result.source_groups, ("source-A", "source-B"))

    def test_duplicate_evidence_identity_rejected(self):
        item = EvidenceItem("a", "source-A", .9, .1)
        with self.assertRaisesRegex(ValueError, "repeated evidence identity"):
            revise_distinct(.5, [item, item])

    def test_same_dependency_group_cannot_masquerade_as_independent(self):
        with self.assertRaisesRegex(ValueError, "dependent evidence"):
            revise_distinct(.5, [EvidenceItem("a", "shared-report", .9, .1),
                                   EvidenceItem("b", "shared-report", .9, .1)])

    def test_invalid_source_and_corrupt_likelihood_rejected(self):
        with self.assertRaises(ValueError): EvidenceItem("", "s", .9, .1)
        with self.assertRaises(ValueError): EvidenceItem("a", "", .9, .1)
        with self.assertRaises(ValueError): EvidenceItem("a", "s", float("nan"), .1)
        with self.assertRaises(ValueError): revise_distinct(float("inf"),
                    [EvidenceItem("a", "s", .9, .1)])

    def test_empty_evidence_cannot_claim_revision(self):
        with self.assertRaisesRegex(ValueError, "one or more"):
            revise_distinct(.5, [])

    def test_probability_contract_rejects_coercion_and_overflow(self):
        for value in (True, False, "0.5", 10**1000, -10**1000, float("nan"), float("inf")):
            with self.subTest(value=repr(value)[:30]):
                with self.assertRaises(ValueError): Prediction("a", value, True, "e")
                with self.assertRaises(ValueError):
                    score([Prediction("a", .5, True, "e")], {"a": True}, abstention_cost=value)
                with self.assertRaises(ValueError): revise(value, .5, .5, "e")
                with self.assertRaises(ValueError): revise(.5, value, .5, "e")
                with self.assertRaises(ValueError): EvidenceItem("e", "g", value, .5)
                with self.assertRaises(ValueError):
                    revise_distinct(value, [EvidenceItem("e", "g", .5, .5)])

    def test_identity_contract_rejects_nonstring_identifiers(self):
        for value in (1, True, b"e"):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError): Prediction(value, .5, True, "e")
                with self.assertRaises(ValueError): Prediction("a", .5, True, value)
                with self.assertRaises(ValueError): revise(.5, .5, .5, value)
                with self.assertRaises(ValueError): EvidenceItem(value, "g", .5, .5)
                with self.assertRaises(ValueError): EvidenceItem("e", value, .5, .5)

if __name__ == '__main__': unittest.main()
