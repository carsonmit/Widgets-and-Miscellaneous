"""
Automatic tests for the Star Battle solver.

Run them from this folder with:
    python -m unittest test_solver.py

Each test sets up a situation and checks the solver behaves as expected.
If everything is fine you'll see "OK" at the end.
"""

import glob
import json
import os
import re
import shutil
import subprocess
import unittest

from solver import StarBattleSolver, check_solution, load_puzzle
from puzzle_generator import generate_puzzle

HERE = os.path.dirname(os.path.abspath(__file__))
NODE = shutil.which("node")   # Node.js runs the web app's JavaScript outside a browser


def run_js(script, data):
    """Run a bit of JavaScript with Node.js, handing it `data`; returns what it prints, as JSON."""
    result = subprocess.run([NODE, "-e", script], input=json.dumps(data), cwd=HERE,
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


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

    @unittest.skipUnless(NODE, "Node.js is not installed")
    def test_web_app_solves_exactly_like_python(self):
        """
        solver.js (the web app) is a translation of solver.py. Both must take
        the same steps, with the same explanations and boards, on every puzzle.
        """
        puzzles = [load_puzzle(p) for p in sorted(glob.glob(os.path.join(HERE, "puzzles", "*.txt")))]
        puzzles += [generate_puzzle(seed=seed) for seed in range(10)]
        expected = [[[s.action, [list(c) for c in s.cells], s.message, s.grid, s.depth,
                      [list(c) for c in s.focus], s.rule]
                     for s in StarBattleSolver(p).solve_steps()] for p in puzzles]
        script = """
            const { StarBattleSolver } = require('./solver.js');
            const puzzles = JSON.parse(require('fs').readFileSync(0, 'utf8'));
            console.log(JSON.stringify(puzzles.map(p => [...new StarBattleSolver(p).solveSteps()]
              .map(s => [s.action, s.cells, s.message, s.grid, s.depth, s.focus, s.rule]))));
        """
        actual = run_js(script, puzzles)
        for i, (want, got) in enumerate(zip(expected, actual)):
            self.assertEqual(got, want, f"puzzle {i} differs")

    @unittest.skipUnless(NODE, "Node.js is not installed")
    def test_examples_have_their_difficulty(self):
        """Each example file's name matches the grade the web app gives it, and the app has the same puzzles."""
        files = sorted(glob.glob(os.path.join(HERE, "puzzles", "example_*.txt")))
        script = """
            const { gradePuzzle } = require('./generator.js');
            const puzzles = JSON.parse(require('fs').readFileSync(0, 'utf8'));
            console.log(JSON.stringify(puzzles.map(p => gradePuzzle(p).difficulty)));
        """
        grades = run_js(script, [load_puzzle(f) for f in files])
        with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
            page = f.read()
        for path, grade in zip(files, grades):
            level = re.search(r"example_\d+_(\w+)\.txt", path).group(1)
            self.assertEqual(grade, level, path)
            self.assertIn(f"{level}: '{' '.join(load_puzzle(path))}'", page, f"index.html's {level} example differs from {path}")

    @unittest.skipUnless(NODE, "Node.js is not installed")
    def test_random_puzzles_have_the_chosen_difficulty(self):
        """The web app's generator returns a puzzle of exactly the difficulty asked for."""
        script = """
            const { generateWithDifficulty, gradePuzzle } = require('./generator.js');
            const { StarBattleSolver } = require('./solver.js');
            const out = ['easy', 'medium', 'hard'].map((d, i) => {
              const { rows } = generateWithDifficulty(d, { seed: 100 + i });
              return [d, gradePuzzle(rows).difficulty, new StarBattleSolver(rows).countSolutions(3)];
            });
            console.log(JSON.stringify(out));
        """
        for wanted, got, solutions in run_js(script, None):
            self.assertEqual(got, wanted)
            self.assertEqual(solutions, 1)

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
