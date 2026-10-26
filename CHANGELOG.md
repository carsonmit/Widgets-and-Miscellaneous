# Changelog

All notable changes to this repository are written down here, newest first.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and version numbers follow
`MAJOR.MINOR.PATCH`: MAJOR for a big redesign, MINOR for a new program or feature, PATCH for fixes and small edits.

Versions 0.1.0 to 0.4.0 were reconstructed from the git history on 2026-10-26; they were never tagged in git.

## [Unreleased]

### Changed
- Star Battle Solver: the example puzzles were re-graded by the new difficulty levels. The old "medium" and "hard"
  examples both needed a guess inside a guess, so the old hard one is now `example_4_expert.txt`, and new medium and
  hard examples were generated and checked.
- Neuron Diagram Maker now has the look of [carsonmit.github.io](https://carsonmit.github.io): the site's colors
  (charcoal and lilac by night, cream and plum by day) and fonts, rounded pill buttons, and the site's sun/moon
  Night/Day switch, which shares its setting with the website. The drawing stays black on paper, and exports are unchanged.
- Neuron Diagram Maker: titles and buttons use Title Case ("Export Image", "Copy Code", "Firing Neuron"), and the
  help text names them the same way.
- Neuron Diagram Maker: on phones the top bar fits in two rows.
- Neuron Diagram Maker has a new icon, designed as a pair with the Star Battle Solver's: neuron c firing into e.
  Home screens show the cream version; the browser tab shows cream in a light browser and charcoal in a dark one.

### Added
- Star Battle Solver is now a web app (`StarBattleSolver/index.html`) for computers, tablets and phones, in the
  look of carsonmit.github.io, with its own home-screen icon (a pair with the Neuron Diagram Maker's). It can be
  installed from the browser's Add to Home Screen and works offline.
- Star Battle Solver: the solver translated into JavaScript (`solver.js`); the tests check it takes exactly the same
  steps, with the same explanations, as `solver.py`.
- Star Battle Solver: four difficulty levels (Easy, Medium, Hard and a new Expert), graded by which of the solver's
  rules a puzzle needs and how deep its guessing goes. **Random Puzzle** lets you pick the level and keeps generating
  until a puzzle really has it (`generator.js`, run in the background by `worker.js`).
- Star Battle Solver: an eraser for touch screens, checks that stop an unfinished or broken puzzle from being solved
  (unpainted cells, the wrong number of regions, regions too small), a warning for puzzles with no answer or several,
  and a question before solving split regions.
- Star Battle Solver: tests for the JavaScript solver, the example difficulties and the random-puzzle difficulties.
- This changelog.

### Removed
- Star Battle Solver: the desktop window (`star_battle_gui.py`); the web app replaces it. `solver.py`,
  `puzzle_generator.py` and the tests stay.

## [0.4.0] - 2026-10-01

### Added
- Neuron Diagram Maker (`NeuronDiagrams/`): a point-and-click editor for the neuron diagrams of the philosophy of
  causation. It exports TikZ code for LaTeX (needing only `\usepackage{tikz}`) or a PNG/SVG image, works with a mouse
  or a finger, and can be installed on an iPad from Safari's Add to Home Screen.

## [0.3.0] - 2026-10-01

### Added
- Star Battle Solver (`StarBattleSolver/`): a solver for 10×10 two-star Star Battle puzzles, with a window where you
  paint in the regions and watch it solve step by step, each step explained in plain English. Also a generator for
  puzzles with exactly one solution, three example puzzles, tests and a README.

## [0.2.0] - 2021-12-26

### Added
- Sudoku solver (`SudokuSolver.py`) with a window to type the puzzle into.

## [0.1.0] - 2021-02-02

### Added
- First small Python programs: name length (`name_length.py`), a directory of the first 46 US presidents
  (`USPresidentsIndex.py`), a quadratic formula solver (`QuadraticFormula.py`), a temperature converter between
  Fahrenheit, Celsius and Kelvin (`TemperatureConverter.py`), and a Scrabble score calculator (`ScrabbleScore.py`).
