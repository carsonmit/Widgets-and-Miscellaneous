"""
Automatic tests for the Star Battle solver.

Run them from this folder with:
    python -m unittest test_solver.py

Each test sets up a situation and checks the solver behaves as expected.
If everything is fine you'll see "OK" at the end.
"""

import glob
import os
import unittest

from solver import StarBattleSolver, check_solution, load_puzzle
from puzzle_generator import generate_puzzle

HERE = os.path.dirname(os.path.abspath(__file__))


class SolverTests(unittest.TestCase):

    def test_examples_solve_correctly(self):
        """Every example puzzle gets a valid answer, and only one exists."""
        files = sorted(glob.glob(os.path.join(HERE, "puzzles", "*.txt")))
        self.assertTrue(files, "no example puzzles found")
        for path in files:
            puzzle = load_puzzle(path)
            answer = StarBattleSolver(puzzle).solve()
            self.assertIsNotNone(answer, path)
            self.assertTrue(check_solution(puzzle, answer), path)
            self.assertEqual(StarBattleSolver(puzzle).count_solutions(limit=3), 1, path)

    def test_without_deep_lookahead_gives_same_answer(self):
        """Switching off Rule 4 changes the route, not the destination."""
        puzzle = load_puzzle(os.path.join(HERE, "puzzles", "example_3_hard.txt"))
        self.assertEqual(StarBattleSolver(puzzle).solve(),
                         StarBattleSolver(puzzle, deep_lookahead=False).solve())

    def test_random_puzzles(self):
        """Generated puzzles have exactly one solution, which the solver finds."""
        for seed in range(3):
            puzzle = generate_puzzle(seed=seed)
            self.assertEqual(StarBattleSolver(puzzle).count_solutions(limit=3), 1)
            self.assertTrue(check_solution(puzzle, StarBattleSolver(puzzle).solve()))

    def test_small_one_star_puzzle(self):
        """The solver also handles other sizes and 1 star per unit."""
        puzzle = generate_puzzle(n=6, stars=1, seed=7)
        answer = StarBattleSolver(puzzle, stars=1).solve()
        self.assertTrue(check_solution(puzzle, answer, stars=1))

    def test_impossible_puzzle(self):
        """
        Region J is just two side-by-side cells, so it can't hold 2 stars
        without them touching. The solver must report "no solution".
        """
        puzzle = ["JJAAAAAAAA",
                  "BBBBBBBBBB",
                  "CCCCCCCCCC",
                  "DDDDDDDDDD",
                  "EEEEEEEEEE",
                  "FFFFFFFFFF",
                  "GGGGGGGGGG",
                  "HHHHHHHHHH",
                  "IIIIIIIIII",
                  "IIIIIIIIII"]
        self.assertIsNone(StarBattleSolver(puzzle).solve())

    def test_bad_input_is_rejected(self):
        """Wrong number of regions or a non-square grid raises an error."""
        with self.assertRaises(ValueError):
            StarBattleSolver(["A" * 10] * 10)          # only 1 region
        with self.assertRaises(ValueError):
            StarBattleSolver(["ABCDEFGHIJ"] * 9)       # 9 rows, not 10

    def test_steps_are_reported(self):
        """The step-by-step mode starts with 'start' and ends with 'solved'."""
        puzzle = load_puzzle(os.path.join(HERE, "puzzles", "example_1_easy.txt"))
        steps = list(StarBattleSolver(puzzle).solve_steps())
        self.assertEqual(steps[0].action, "start")
        self.assertEqual(steps[-1].action, "solved")
        for step in steps:
            self.assertEqual(len(step.grid), 10)       # every step has a board


if __name__ == "__main__":
    unittest.main()
