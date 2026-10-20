import unittest
from dataclasses import replace

from humility.core import Prediction
from humility.experiment import commit_predictions, score_committed


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

    def test_one_shot_iterable_scored_once(self):
        r = score_committed(self.commit, iter(self.rows), self.labels)
        self.assertEqual(r["metrics"]["n"], 2)

    def test_nonnumeric_confidence_rejected(self):
        with self.assertRaisesRegex(ValueError, 'numeric confidence'):
            commit_predictions('x', (replace(self.rows[0], probability_true=True),))

    def test_outcome_digest_changes_without_qualifying_custody(self):
        r1 = score_committed(self.commit, self.rows, self.labels)
        r2 = score_committed(self.commit, self.rows, {'a': False, 'b': True})
        self.assertNotEqual(r1['outcome_digest'], r2['outcome_digest'])
        self.assertFalse(r2['independent_evaluator_verified'])


if __name__ == '__main__':
    unittest.main()
