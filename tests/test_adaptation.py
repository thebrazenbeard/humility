import unittest
from humility.adaptation import OnlineCalibrator


class AdaptiveCalibrationTests(unittest.TestCase):
    def test_predictions_change_only_after_feedback(self):
        monitor = OnlineCalibrator(prior_weight=2)
        first = monitor.forecast("a", .9)
        self.assertEqual(first.adjusted_probability, .9)
        with self.assertRaises(ValueError): monitor.forecast("b", .9)
        monitor.observe("a", False)
        second = monitor.forecast("b", .9)
        self.assertLess(second.adjusted_probability, .9)
        self.assertEqual(second.prior_observations, 1)

    def test_brier_improves_on_consistent_miscalibration(self):
        monitor = OnlineCalibrator(window=20, prior_weight=2)
        results = []
        for i in range(80):
            monitor.forecast(str(i), .9)
            results.append(monitor.observe(str(i), i % 2 == 0))
        tail = results[-30:]
        self.assertLess(sum(r["adjusted_brier"] for r in tail),
                        sum(r["raw_brier"] for r in tail))

    def test_shift_regression_is_reported_not_hidden(self):
        monitor = OnlineCalibrator(window=20, prior_weight=2)
        for i in range(40):
            monitor.forecast(str(i), .9)
            monitor.observe(str(i), i % 2 == 0)
        errors = []
        for i in range(40, 50):
            monitor.forecast(str(i), .9)
            errors.append(monitor.observe(str(i), True))
        self.assertGreater(sum(r["adjusted_brier"] for r in errors[:5]),
                           sum(r["raw_brier"] for r in errors[:5]))

    def test_replay_and_invalid_feedback_rejected(self):
        monitor = OnlineCalibrator()
        monitor.forecast("a", .6)
        with self.assertRaises(ValueError): monitor.observe("a", 1)
        monitor.observe("a", True)
        with self.assertRaises(ValueError): monitor.observe("a", False)
        with self.assertRaises(ValueError): monitor.forecast("a", .6)

    def test_bad_configuration_rejected(self):
        for kwargs in ({"bins": 1}, {"window": 0}, {"prior_weight": 0},
                       {"prior_weight": float("nan")}):
            with self.assertRaises(ValueError): OnlineCalibrator(**kwargs)

    def test_not_independently_qualified(self):
        self.assertFalse(hasattr(OnlineCalibrator, "independent_evaluator_verified"))


if __name__ == "__main__":
    unittest.main()