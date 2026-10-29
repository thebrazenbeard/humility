import unittest
from dataclasses import dataclass, replace
from math import nan

from humility.core import Prediction
from humility.experiment import commit_predictions, score_committed


@dataclass(frozen=True)
class TaggedPrediction(Prediction):
    tag: str = 'local-metadata'


class PredictionProtocolTests(unittest.TestCase):
    def setUp(self):
        self.rows = (Prediction('b', .2, None, 'report-b'),
                     Prediction('a', .85, True, 'report-a'))
        self.labels = {'a': True, 'b': False}
        self.commit = commit_predictions('round-1', self.rows)

    def test_order_independent_commitment(self):
        self.assertEqual(self.commit, commit_predictions('round-1', tuple(reversed(self.rows))))

    def test_actual_outcome_scoring_and_scope_flags(self):
        result = score_committed(self.commit, self.rows, self.labels)
        self.assertEqual(result['metrics']['coverage'], .5)
        self.assertEqual(result['metrics']['n'], 2)
        self.assertEqual(result['prediction_digest'], self.commit.digest)
        self.assertFalse(result['independent_evaluator_verified'])
        self.assertFalse(result['pre_outcome_timing_verified'])

    def test_post_commit_probability_edit_rejected(self):
        altered = (self.rows[0], replace(self.rows[1], probability_true=.99))
        with self.assertRaisesRegex(ValueError, 'commitment mismatch'):
            score_committed(self.commit, altered, self.labels)

    def test_post_commit_evidence_relabel_rejected(self):
        altered = (self.rows[0], replace(self.rows[1], evidence_id='different'))
        with self.assertRaisesRegex(ValueError, 'commitment mismatch'):
            score_committed(self.commit, altered, self.labels)

    def test_duplicate_and_nonstr_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            commit_predictions('a', (self.rows[0], self.rows[0]))
        with self.assertRaisesRegex(ValueError, 'nonempty string'):
            commit_predictions('a', (replace(self.rows[0], case_id=7),))

    def test_labels_must_match_exact_cases(self):
        with self.assertRaises(ValueError):
            score_committed(self.commit, self.rows, {'a': True, 'c': False})

    def test_challenge_switch_rejected(self):
        bogus = replace(self.commit, challenge_id='new-round')
        with self.assertRaisesRegex(ValueError, 'commitment mismatch'):
            score_committed(bogus, self.rows, self.labels)
        with self.assertRaisesRegex(ValueError, 'nonempty challenge'):
            score_committed(replace(self.commit, challenge_id=0), self.rows, self.labels)

    def test_forged_commitment_field_types_rejected(self):
        class AlwaysEqual:
            def __eq__(self, other):
                return True

        single = commit_predictions('single', (self.rows[0],))
        for field, invalid in (('count', True), ('count', 1.0),
                               ('count', -1), ('count', 0),
                               ('digest', AlwaysEqual()),
                               ('schema', AlwaysEqual())):
            with self.subTest(field=field, invalid=invalid):
                forged = replace(single, **{field: invalid})
                with self.assertRaises(ValueError):
                    score_committed(forged, (self.rows[0],), {'b': False})

    def test_one_shot_iterable_scored_once(self):
        r = score_committed(self.commit, iter(self.rows), self.labels)
        self.assertEqual(r["metrics"]["n"], 2)

    def test_nonnumeric_confidence_rejected(self):
        with self.assertRaisesRegex(ValueError, 'numeric confidence'):
            commit_predictions('x', (replace(self.rows[0], probability_true=True),))

    def test_commitment_rejects_corrupted_frozen_prediction_fields(self):
        for field, invalid in (("probability_true", 2.0),
                               ("probability_true", -.01),
                               ("probability_true", nan),
                               ("decision", "yes"),
                               ("decision", 1),
                               ("case_id", ""),
                               ("evidence_id", "")):
            with self.subTest(field=field, invalid=invalid):
                row = Prediction("a", .8, True, "report-a")
                object.__setattr__(row, field, invalid)
                with self.assertRaises(ValueError):
                    commit_predictions('corrupted', (row,))

    def test_commitment_preserves_valid_prediction_subclasses(self):
        row = TaggedPrediction('a', .8, True, 'report-a')
        base = Prediction('a', .8, True, 'report-a')
        commitment = commit_predictions('subtype', (row,))
        # V1 includes dataclass-subclass fields in the digest. Preserve that
        # existing serialization contract even though scoring uses core fields.
        self.assertNotEqual(commitment, commit_predictions('subtype', (base,)))
        self.assertEqual(score_committed(commitment, (row,), {'a': True})['metrics']['brier'],
                         (1 - .8)**2)

    def test_scoring_uses_the_committed_snapshot_not_subclass_rereads(self):
        class ChangingPrediction(Prediction):
            def __getattribute__(self, name):
                if name == 'probability_true':
                    try:
                        reads = object.__getattribute__(self, '_probability_reads')
                    except AttributeError:
                        return object.__getattribute__(self, name)
                    object.__setattr__(self, '_probability_reads', reads + 1)
                    return .8 if reads < 2 else .2
                return object.__getattribute__(self, name)

        row = ChangingPrediction('a', .8, True, 'report-a')
        object.__setattr__(row, '_probability_reads', 0)
        commitment = commit_predictions('subclass-reread', (row,))
        receipt = score_committed(commitment, (row,), {'a': True})
        self.assertAlmostEqual(receipt['metrics']['brier'], .04)
        self.assertEqual(object.__getattribute__(row, '_probability_reads'), 2)

    def test_outcome_digest_and_scoring_use_one_plain_dict_snapshot(self):
        class Liar(dict):
            def __getitem__(self, case_id):
                return not super().__getitem__(case_id)

        expected = score_committed(self.commit, self.rows, self.labels)
        observed = score_committed(self.commit, self.rows, Liar(self.labels))
        self.assertEqual(observed['metrics'], expected['metrics'])
        self.assertEqual(observed['outcome_digest'], expected['outcome_digest'])

    def test_receipt_uses_verified_commitment_snapshot(self):
        class CommitmentMutator(Prediction):
            def __getattribute__(self, name):
                if name == 'probability_true':
                    try:
                        target = object.__getattribute__(self, '_target_commitment')
                    except AttributeError:
                        pass
                    else:
                        object.__setattr__(target, 'digest', '0' * 64)
                return object.__getattribute__(self, name)

        row = CommitmentMutator('a', .8, True, 'report-a')
        commitment = commit_predictions('mutation',
                                        (Prediction('a', .8, True, 'report-a'),))
        expected_digest = commitment.digest
        object.__setattr__(row, '_target_commitment', commitment)
        receipt = score_committed(commitment, (row,), {'a': True})
        self.assertEqual(receipt['prediction_digest'], expected_digest)
        self.assertAlmostEqual(receipt['metrics']['brier'], .04)
        self.assertEqual(commitment.digest, '0' * 64)  # caller's object was mutated

    def test_outcome_digest_changes_without_qualifying_custody(self):
        r1 = score_committed(self.commit, self.rows, self.labels)
        r2 = score_committed(self.commit, self.rows, {'a': False, 'b': True})
        self.assertNotEqual(r1['outcome_digest'], r2['outcome_digest'])
        self.assertFalse(r2['independent_evaluator_verified'])


if __name__ == '__main__':
    unittest.main()
