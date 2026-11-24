import unittest
from humility.blind_reader import CandidateReading, review


class BlindReaderTests(unittest.TestCase):
    def test_weather_scene_records_competing_grounded_readings_without_claiming_truth(self):
        utterance = ('A teenage boy was trying to keep a plastic bag over a sleeping '
                     "child's head while another adult fastened a dry coat.")
        readings = [
            CandidateReading('shelter', 'Bag held above face as a rain cover',
                             ('plastic bag over a sleeping',), 'DESCRIPTION',
                             ('bag suspended above head',)),
            CandidateReading('danger', 'Bag enclosing head and obstructing breathing',
                             ('plastic bag over a sleeping',), 'DESCRIPTION',
                             ('bag touches face and seals around head',)),
        ]
        result = review(utterance, 'DESCRIPTION', readings)
        self.assertEqual(result.status, 'REVIEW_REQUIRED')
        self.assertEqual(result.alternative_reading_ids, ('shelter', 'danger'))
        self.assertEqual(result.unverified_plausibility, True)
        self.assertEqual(result.uncertain_assumptions, ('shelter', 'danger'))
        self.assertEqual(result.action_effect, 'NONE')

    def test_abstract_thought_must_not_be_silently_promoted_to_action(self):
        utterance = "I'm thinking about thinking about it abstractly."
        readings = [
            CandidateReading('abstract', 'Meta-level consideration', ('thinking about thinking',), 'ABSTRACT_CONSIDERATION'),
            CandidateReading('plan', 'Action already prepared', ('thinking about thinking',), 'PREPARED_ACTION'),
        ]
        result = review(utterance, 'ABSTRACT_CONSIDERATION', readings)
        self.assertEqual(result.modality_mismatches, ('plan',))
        self.assertEqual(result.status, 'REVIEW_REQUIRED')

    def test_unanchored_evidence_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'not found'):
            review('I might be wrong', 'ASSERTION', [CandidateReading('r', 'Confident', ('I am certain',), 'ASSERTION')])

    def test_one_reading_does_not_prove_ambiguity_or_accuracy(self):
        result = review('We can revise', 'ASSERTION', [CandidateReading('r', 'Revision is possible', ('revise',), 'ASSERTION')])
        self.assertEqual(result.status, 'NO_CONFLICT_OBSERVED')
        self.assertTrue(result.unverified_plausibility)

    def test_rejects_duplicate_and_mutated_candidates(self):
        a = CandidateReading('same', 'one', ('a',), 'ASSERTION')
        b = CandidateReading('same', 'two', ('a',), 'ASSERTION')
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            review('a', 'ASSERTION', [a, b])
        object.__setattr__(a, 'modality', 'MAGIC')
        with self.assertRaises(ValueError):
            review('a', 'ASSERTION', [a])

    def test_mutated_sequence_fields_are_rejected_without_coercion(self):
        # A caller can change frozen dataclass fields with object.__setattr__.
        # Neither an evidence quote nor a source assumption may silently
        # become one-character tokens when converted from str to tuple.
        for field, malformed in (('quoted_evidence', 'bag'),
                                 ('unstated_assumptions', 'maybe')):
            reading = CandidateReading('r', 'Bag is overhead',
                                       ('bag',), 'DESCRIPTION', ('maybe',))
            object.__setattr__(reading, field, malformed)
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    review('bag maybe', 'DESCRIPTION', [reading])

    def test_rejects_invalid_types_and_vacuous_text(self):
        for t in ('', ' ', 42):
            with self.assertRaises(ValueError):
                review(t, 'ASSERTION', [CandidateReading('r', 'x', ('x',), 'ASSERTION')])
        with self.assertRaises(ValueError):
            review('x', 'ASSERTION', [])
        with self.assertRaises(ValueError):
            CandidateReading('r', 'x', ('x',), 'ASSERTION', (123,))
        with self.assertRaises(ValueError):
            CandidateReading('r', 'x', ('x',), 'NOT_REAL')

if __name__ == '__main__':
    unittest.main()
