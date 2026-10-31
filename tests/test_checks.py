import unittest

from eurocode3.checks import DesignInput, run_checks


class ChecksTest(unittest.TestCase):
    def test_example_has_expected_checks(self):
        data = DesignInput(
            "test", "C1", "S275", 275, 430, 5000, 80e6, 20e6, 400e3, 150e3,
            3000, 3000, 1, 1, -100, 20, 5, 15
        )
        report = run_checks(data)
        self.assertEqual(len(report.checks), 6)
        self.assertTrue(all(item.resistance > 0 for item in report.checks))

    def test_invalid_section_is_rejected(self):
        data = DesignInput(
            "test", "C1", "S275", 275, 430, 0, 80e6, 20e6, 400e3, 150e3,
            3000, 3000, 1, 1
        )
        with self.assertRaises(ValueError):
            run_checks(data)


if __name__ == "__main__":
    unittest.main()
