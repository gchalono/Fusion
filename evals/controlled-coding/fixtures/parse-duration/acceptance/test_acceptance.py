import copy, unittest
from solution import parse_duration

class Acceptance(unittest.TestCase):
    def test_case_0(self):
        args = ['2h 3m 4s']
        before = copy.deepcopy(args)
        self.assertEqual(parse_duration(*args), 7384)
        self.assertEqual(args, before)
    def test_case_1(self):
        args = ['1m2m']
        before = copy.deepcopy(args)
        self.assertEqual(parse_duration(*args), 180)
        self.assertEqual(args, before)
    def test_case_2(self):
        args = ['0s']
        before = copy.deepcopy(args)
        self.assertEqual(parse_duration(*args), 0)
        self.assertEqual(args, before)
    def test_case_3(self):
        args = [' 2s ']
        before = copy.deepcopy(args)
        self.assertEqual(parse_duration(*args), 2)
        self.assertEqual(args, before)
    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_duration(*[''])
    def test_invalid_forms(self):
        for text in ['-1s', '1.2h', '1x', '1s garbage', '']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_duration(text)
