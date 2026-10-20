import unittest
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


if __name__ == "__main__":
    unittest.main()