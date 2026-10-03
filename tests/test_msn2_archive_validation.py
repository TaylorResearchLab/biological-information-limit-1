"""Tests of archive-validation guards, separate from scientific verification."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('msn2_derived_validator', ROOT / 'tools/verify_msn2_derived.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ComparisonGuards(unittest.TestCase):
    def test_identical_nested_records(self):
        record = {'exact': '7/9', 'counts': [1, 2, 3, 4], 'value': 0.5, 'label': None}
        errors = []
        validator.compare(record, record.copy(), 'test', errors)
        self.assertEqual(errors, [0.0])

    def test_float_tolerance_is_explicit(self):
        errors = []
        validator.compare(0.5, 0.5 + 1e-13, 'test', errors)
        self.assertGreater(errors[0], 0.0)
        with self.assertRaises(ValueError):
            validator.compare(0.5, 0.5 + 1e-7, 'test', [])

    def test_discrete_and_exact_values_are_strict(self):
        for left, right in [(1, 2), (1, 1.0), (True, 1), ('7/9', '0.7777777778')]:
            with self.subTest(left=left, right=right), self.assertRaises(ValueError):
                validator.compare(left, right, 'test', [])

    def test_missing_fields_and_rows_are_rejected(self):
        for left, right in [({'a': 1}, {'b': 1}), ([1, 2], [1]), ({'a': 1}, None)]:
            with self.subTest(left=left, right=right), self.assertRaises(ValueError):
                validator.compare(left, right, 'test', [])

    def test_nonfinite_values_are_rejected(self):
        for left, right in [(float('nan'), 0.0), (0.0, float('inf')), (float('inf'), float('inf'))]:
            with self.subTest(left=left, right=right), self.assertRaises(ValueError):
                validator.compare(left, right, 'test', [])

    def test_failed_requirement_raises(self):
        validator.require(True, 'accepted')
        with self.assertRaisesRegex(ValueError, 'rejected'):
            validator.require(False, 'rejected')


if __name__ == '__main__':
    unittest.main()
