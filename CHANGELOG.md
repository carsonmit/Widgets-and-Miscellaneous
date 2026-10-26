# Changelog

All notable changes to this repository are written down here, newest first.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and version numbers follow
`MAJOR.MINOR.PATCH`: MAJOR for a big redesign, MINOR for a new program or feature, PATCH for fixes and small edits.

Versions 0.1.0 to 0.4.0 were reconstructed from the git history on 2026-10-26; they were never tagged in git.

## [Unreleased]

### Changed
- Neuron Diagram Maker now has the look of [carsonmit.github.io](https://carsonmit.github.io): the site's colors
  (charcoal and lilac by night, cream and plum by day) and fonts, rounded pill buttons, and the site's sun/moon
  Night/Day switch, which shares its setting with the website. The drawing stays black on paper, and exports are unchanged.
- Neuron Diagram Maker: titles and buttons use Title Case ("Export Image", "Copy Code", "Firing Neuron"), and the
  help text names them the same way.
- Neuron Diagram Maker: on phones the top bar fits in two rows.

### Added
- This changelog.

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
