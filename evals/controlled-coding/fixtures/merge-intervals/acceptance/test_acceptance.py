import copy, unittest
from solution import merge_intervals

class Acceptance(unittest.TestCase):
    def test_case_0(self):
        args = [[[5, 7], [1, 3], [3, 4]]]
        before = copy.deepcopy(args)
        self.assertEqual(merge_intervals(*args), [[1, 4], [5, 7]])
        self.assertEqual(args, before)
    def test_case_1(self):
        args = [[]]
        before = copy.deepcopy(args)
        self.assertEqual(merge_intervals(*args), [])
        self.assertEqual(args, before)
    def test_case_2(self):
        args = [[[1, 2], [1, 2], [2, 8]]]
        before = copy.deepcopy(args)
        self.assertEqual(merge_intervals(*args), [[1, 8]])
        self.assertEqual(args, before)
    def test_invalid(self):
        with self.assertRaises(ValueError):
            merge_intervals(*[[[4, 2]]])
