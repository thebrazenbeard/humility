import unittest
from unittest.mock import patch

from humility.prequential import evaluate_stream


class EvaluatorTruthFeedbackSeparationTests(unittest.TestCase):
    def setUp(self):
        self.rows = [(f"case-{i}", 0.9, True,
                      "train" if i < 10 else "later") for i in range(20)]

    def test_default_and_explicit_clean_feedback_agree(self):
        original = evaluate_stream(self.rows)
        explicit = evaluate_stream(self.rows, feedback_overrides={})
        self.assertEqual(original["phases"], explicit["phases"])
        self.assertEqual(explicit["feedback_divergent_count"], 0)
        self.assertFalse(explicit["independent_label_custody_verified"])

    def test_poison_final_feedback_cannot_change_scored_truth(self):
        clean = evaluate_stream(self.rows)
        corrupt = evaluate_stream(self.rows, feedback_overrides={"case-19": False})
        for phase in ("train", "later"):
            self.assertEqual(clean["phases"][phase]["raw_brier"],
                             corrupt["phases"][phase]["raw_brier"])
            self.assertEqual(clean["phases"][phase]["adjusted_brier"],
                             corrupt["phases"][phase]["adjusted_brier"])
        self.assertEqual(corrupt["feedback_divergent_count"], 1)
        self.assertEqual(corrupt["feedback_override_count"], 1)
        self.assertEqual(corrupt["score_truth_origin"], "EVALUATOR_LOCAL_UNAUTHENTICATED")
        self.assertEqual(corrupt["feedback_origin"], "SIMULATED_UNTRUSTED")

    def test_corrupted_early_feedback_can_hurt_later_clean_truth_score(self):
        clean = evaluate_stream(self.rows)
        corrupt = evaluate_stream(
            self.rows,
            feedback_overrides={f"case-{i}": False for i in range(10)},
        )
        self.assertEqual(clean["phases"]["later"]["n"], corrupt["phases"]["later"]["n"])
        self.assertGreater(corrupt["phases"]["later"]["adjusted_brier"],
                           clean["phases"]["later"]["adjusted_brier"])
        self.assertEqual(corrupt["feedback_divergent_count"], 10)

    def test_invalid_overrides_rejected_before_child_process(self):
        invalid = ({"absent": False}, {"case-0": 0}, {"case-0": 1},
                   {"case-0": 0.0}, {2: False}, [("case-0", False)])
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with patch("humility.prequential.subprocess.Popen",
                           side_effect=AssertionError("worker must not start")):
                    with self.assertRaises(ValueError):
                        evaluate_stream(self.rows, feedback_overrides=overrides)

    def test_repeated_case_id_rejected_before_child_process(self):
        with patch("humility.prequential.subprocess.Popen",
                   side_effect=AssertionError("worker must not start")):
            with self.assertRaises(ValueError):
                evaluate_stream([("same", 0.9, True, "a"), ("same", 0.9, True, "b")],
                                feedback_overrides={"same": False})


if __name__ == "__main__":
    unittest.main()
