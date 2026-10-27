import unittest
from math import inf, nan
from unittest.mock import patch
from humility.prequential import evaluate_stream


class SeparatedCalibrationTests(unittest.TestCase):
    def test_miscalibration_and_distribution_shift_both_measured(self):
        rows = [(str(i), .9, i % 2 == 0, "stable") for i in range(80)]
        rows += [(str(i), .9, True, "shift") for i in range(80, 90)]
        result = evaluate_stream(rows)
        self.assertTrue(result["separate_process_observed"])
        self.assertTrue(result["prediction_before_label_protocol"])
        self.assertFalse(result["independent_label_custody_verified"])
        self.assertFalse(result["sandbox_isolation_verified"])
        self.assertLess(result["phases"]["stable"]["adjusted_brier"],
                        result["phases"]["stable"]["raw_brier"])
        self.assertGreater(result["phases"]["shift"]["adjusted_brier"],
                           result["phases"]["shift"]["raw_brier"])

    def test_caller_does_not_get_to_repeat_case(self):
        with self.assertRaises(ValueError):
            evaluate_stream([("x", .7, True, "a"), ("x", .7, False, "b")])

    def test_no_data_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_stream([])

    def test_bad_label_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_stream([("x", .6, 1, "a")])

    def test_untrusted_source_claim_is_not_verified(self):
        result = evaluate_stream([("x", .6, True, "single")])
        self.assertFalse(result["independent_label_custody_verified"])
        self.assertEqual(result["phases"]["single"]["n"], 1)

    def test_malformed_cases_rejected_as_validation_errors_before_launch(self):
        invalid_batches = [
            [()], [None], [("only",)],
            [("x", .5, True, "a"), ("y", False, False, "b")],
            [("x", .5, True, "a"), ("y", nan, True, "b")],
            [("x", .5, True, "a"), ("y", inf, True, "b")],
            [("x", .5, True, "a"), ("y", -0.1, True, "b")],
            [("x", .5, True, "a"), ("y", 1.1, True, "b")],
            [("x", .5, True, "a"), ("y", 10**1000, True, "b")],
        ]
        for cases in invalid_batches:
            with self.subTest(cases=cases):
                with patch("humility.prequential.subprocess.Popen") as popen:
                    with self.assertRaises(ValueError):
                        evaluate_stream(cases)
                    popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
