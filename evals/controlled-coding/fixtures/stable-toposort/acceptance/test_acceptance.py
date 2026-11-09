import copy, unittest
from solution import stable_toposort

class Acceptance(unittest.TestCase):
    def test_case_0(self):
        args = [['c', 'b', 'a'], [['a', 'c']]]
        before = copy.deepcopy(args)
        self.assertEqual(stable_toposort(*args), ['b', 'a', 'c'])
        self.assertEqual(args, before)
    def test_case_1(self):
        args = [[], []]
        before = copy.deepcopy(args)
        self.assertEqual(stable_toposort(*args), [])
        self.assertEqual(args, before)
    def test_case_2(self):
        args = [['a', 'b'], [['a', 'b'], ['a', 'b']]]
        before = copy.deepcopy(args)
        self.assertEqual(stable_toposort(*args), ['a', 'b'])
        self.assertEqual(args, before)
    def test_invalid(self):
        with self.assertRaises(ValueError):
            stable_toposort(*[['a'], [['a', 'a']]])
