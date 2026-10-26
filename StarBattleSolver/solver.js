/*
================================================================================
 STAR BATTLE SOLVER  -  the "brain", in JavaScript (for the web app)
================================================================================
This is a line-by-line translation of solver.py, so the web app solves a
puzzle in exactly the same steps, with the same explanations, as the Python
version. solver.py has the long, friendly explanation of every rule; the
comments here are shorter and point back to it. If you change one file,
change the other too: test_solver.py checks that both give identical steps.

THE RULES OF STAR BATTLE
    Place stars so that every row, every column and every region has exactly
    2 stars (or 1 on small puzzles), and no two stars touch, not even
    diagonally.

HOW TO USE IT
    const solver = new StarBattleSolver(["AABB...", ...], 2);
    for (const step of solver.solveSteps()) { ...draw step... }
    // or: solver.solve()  -> rows of true/false, or null if impossible

Every cell is UNKNOWN, STAR or BLANK (a crossed-out cell). Inside, a cell is
one number: row * n + column, so the top-left cell is 0 and the next row
starts at n.

A note for readers new to JavaScript: a function written `function*` is a
"generator", the same idea as a Python function that uses `yield`. It hands
back one report at a time and pauses until someone asks for the next one.
`yield*` is Python's `yield from`.
================================================================================
*/
'use strict';

const UNKNOWN = 0;   // not decided yet
const STAR = 1;      // definitely a star
const BLANK = 2;     // definitely NOT a star

/** comb(5, 2) = 10: the number of ways to pick k things from n. */
function comb(n, k) {
  if (k < 0 || k > n) return 0;
  let result = 1;
  for (let i = 1; i <= k; i++) result = result * (n - k + i) / i;
  return Math.round(result);
}

/** Python-style comparison of two [ways, -impact] pairs. */
function lessThan(a, b) {
  return a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);
}

class StarBattleSolver {
  /**
   * regions - a list of rows, each a string (or list) of region labels.
   * stars   - stars per row / column / region (2 for 10 x 10).
   * deepLookahead - whether to use Rule 4 (the generator switches it off for speed).
   */
  constructor(regions, stars = 2, deepLookahead = true) {
    this.n = regions.length;
    this.stars = stars;
    for (const row of regions) {
      if (row.length !== this.n) {
        throw new Error(`The grid must be square: every row needs exactly ${this.n} cells.`);
      }
    }
    // Give every region label a number 0, 1, 2, ... in sorted order.
    const labels = [...new Set(regions.flatMap(row => [...row].map(String)))].sort();
    if (labels.length !== this.n) {
      throw new Error(`A ${this.n}x${this.n} puzzle needs exactly ${this.n} regions, but ${labels.length} were found.`);
    }
    this.labels = labels;
    const number = new Map(labels.map((label, i) => [label, i]));
    this.regionOf = [];
    for (let r = 0; r < this.n; r++) {
      for (let c = 0; c < this.n; c++) this.regionOf.push(number.get(String(regions[r][c])));
    }

    // Units: every row, every column, every region (each must hold `stars` stars).
    const n = this.n, all = n * n;
    this.units = [];
    for (let r = 0; r < n; r++) this.units.push({ name: `row ${r + 1}`, cells: range(n).map(c => r * n + c) });
    for (let c = 0; c < n; c++) this.units.push({ name: `column ${c + 1}`, cells: range(n).map(r => r * n + c) });
    labels.forEach((label, k) => {
      this.units.push({ name: `region ${label}`, cells: range(all).filter(i => this.regionOf[i] === k) });
    });
    this.firstRegionUnit = 2 * n;

    // unitsOf[cell] = the 3 units (row, column, region) a cell belongs to.
    this.unitsOf = range(all).map(() => []);
    this.units.forEach((unit, u) => unit.cells.forEach(cell => this.unitsOf[cell].push(u)));

    // neighbours[cell] = the up-to-8 touching cells. A star rules all of them out.
    this.neighbours = range(all).map(cell => {
      const r = Math.floor(cell / n), c = cell % n, touching = [];
      for (let dr = -1; dr <= 1; dr++) {
        for (let dc = -1; dc <= 1; dc++) {
          if (dr === 0 && dc === 0) continue;
          const rr = r + dr, cc = c + dc;
          if (rr >= 0 && rr < n && cc >= 0 && cc < n) touching.push(rr * n + cc);
        }
      }
      return touching.sort((a, b) => a - b);
    });
    this.neighbourSets = this.neighbours.map(list => new Set(list));

    this.deepLookahead = deepLookahead;
    this.quiet = false;        // true while Rule 4 runs a silent experiment
    this.guesses = 0;
    this.backtracks = 0;
    this.solutions = [];
  }

  // ---- Small helpers -------------------------------------------------------
  static cap(text) { return text[0].toUpperCase() + text.slice(1); }

  name(cell) {
    return `row ${Math.floor(cell / this.n) + 1}, column ${cell % this.n + 1}`;
  }

  rc(cells) { return cells.map(cell => [Math.floor(cell / this.n), cell % this.n]); }

  snapshot(grid) { return range(this.n).map(r => grid.slice(r * this.n, (r + 1) * this.n)); }

  /** Package up a report. action: start / star / blank / guess / backtrack / contradiction / solved / failed */
  step(action, cells, message, grid, depth) {
    if (this.quiet) return { action, cells: [], message, grid: null, depth };
    return { action, cells: this.rc(cells), message, grid: this.snapshot(grid), depth };
  }

  /** Can `needed` non-touching stars be placed among these open cells? */
  canFit(cells, needed) {
    if (needed <= 0) return true;
    if (cells.length < needed) return false;
    const first = cells[0], rest = cells.slice(1), touching = this.neighbourSets[first];
    if (this.canFit(rest.filter(c => !touching.has(c)), needed - 1)) return true;
    return this.canFit(rest, needed);
  }

  /** Star on `cell`, neighbours crossed out. Returns the crossed cells, or null if two stars would touch. */
  placeStar(grid, cell) {
    grid[cell] = STAR;
    const crossed = [];
    for (const nb of this.neighbours[cell]) {
      if (grid[nb] === STAR) return null;
      if (grid[nb] === UNKNOWN) { grid[nb] = BLANK; crossed.push(nb); }
    }
    return crossed;
  }

  /** [stars still needed, open cells] for one unit. */
  status(grid, unit) {
    let have = 0;
    const open = [];
    for (const cell of unit.cells) {
      if (grid[cell] === STAR) have++;
      else if (grid[cell] === UNKNOWN) open.push(cell);
    }
    return [this.stars - have, open];
  }

  // ==========================================================================
  //  THE LOGIC RULES. Each returns "progress", "stuck" or "broken".
  // ==========================================================================

  /** RULE 1 - COUNTING: full units, units with no room, exact fits. */
  *ruleCounting(grid, depth) {
    const cap = StarBattleSolver.cap;
    for (const unit of this.units) {
      const [needed, open] = this.status(grid, unit);
      if (needed < 0) {
        yield this.step('contradiction', [], `${unit.name} has too many stars - this can't be right.`, grid, depth);
        return 'broken';
      }
      if (needed === 0 && open.length) {
        for (const cell of open) grid[cell] = BLANK;
        yield this.step('blank', open, `${cap(unit.name)} already has its ${this.stars} star(s), so the rest of it is crossed out.`, grid, depth);
        return 'progress';
      }
      if (needed > 0 && !this.canFit(open, needed)) {
        yield this.step('contradiction', open, `${cap(unit.name)} needs ${needed} more star(s) but there's no room for them without stars touching.`, grid, depth);
        return 'broken';
      }
      if (needed > 0 && needed === open.length) {
        for (const cell of open) {
          if (this.placeStar(grid, cell) === null) {
            yield this.step('contradiction', [cell], `Two stars would touch in ${unit.name}.`, grid, depth);
            return 'broken';
          }
        }
        yield this.step('star', open, `${cap(unit.name)} needs ${needed} more star(s) and has exactly ${needed} open cell(s) left, so they all get stars (and their neighbours are crossed out).`, grid, depth);
        return 'progress';
      }
    }
    return 'stuck';
  }

  /** RULE 2 - SQUEEZE: N regions inside N rows (or columns), or N rows fed by only N regions. */
  *ruleSqueeze(grid, depth) {
    const n = this.n, regionUnits = this.units.slice(this.firstRegionUnit);
    const directions = [
      ['rows', cell => Math.floor(cell / n), this.units.slice(0, n)],
      ['columns', cell => cell % n, this.units.slice(n, 2 * n)],
    ];
    for (const [direction, lineOf, lineCells] of directions) {
      // For each region, which lines it still has open cells in, as on/off bits.
      const masks = regionUnits.map(unit => {
        let mask = 0;
        for (const cell of unit.cells) if (grid[cell] !== BLANK) mask |= 1 << lineOf(cell);
        return mask;
      });
      for (let start = 0; start < n; start++) {
        let bandMask = 0;
        for (let end = start; end < n - 1; end++) {
          bandMask |= 1 << end;
          const width = end - start + 1;
          const inside = range(n).filter(k => masks[k] && !(masks[k] & ~bandMask));
          const touching = range(n).filter(k => masks[k] & bandMask);
          if (inside.length < width && width < touching.length) continue;

          const bandText = width > 1 ? `${direction} ${start + 1}-${end + 1}` : `${direction.slice(0, -1)} ${start + 1}`;
          if (inside.length > width) {
            yield this.step('contradiction', [], `${inside.length} regions are squeezed into just ${bandText} - not enough stars to go round.`, grid, depth);
            return 'broken';
          }
          if (touching.length < width) {
            yield this.step('contradiction', [], `Only ${touching.length} region(s) can supply stars to ${bandText}, which needs more than that.`, grid, depth);
            return 'broken';
          }
          if (inside.length === width) {
            const toBlank = [];
            for (let line = start; line <= end; line++) {
              for (const cell of lineCells[line].cells) {
                if (grid[cell] === UNKNOWN && !inside.includes(this.regionOf[cell])) toBlank.push(cell);
              }
            }
            if (toBlank.length) {
              for (const cell of toBlank) grid[cell] = BLANK;
              const names = inside.map(k => this.labels[k]).join(', ');
              yield this.step('blank', toBlank, `Squeeze: region(s) ${names} fit entirely inside ${bandText}, so they use up all of its stars. Other cells there are crossed out.`, grid, depth);
              return 'progress';
            }
          }
          if (touching.length === width) {
            const toBlank = [];
            for (const k of touching) {
              for (const cell of regionUnits[k].cells) {
                if (grid[cell] === UNKNOWN && !((1 << lineOf(cell)) & bandMask)) toBlank.push(cell);
              }
            }
            if (toBlank.length) {
              for (const cell of toBlank) grid[cell] = BLANK;
              const names = touching.map(k => this.labels[k]).join(', ');
              yield this.step('blank', toBlank, `Squeeze: ${bandText} can only get stars from region(s) ${names}, which fills those regions up. Their cells outside are crossed out.`, grid, depth);
              return 'progress';
            }
          }
        }
      }
    }
    return 'stuck';
  }

  /** RULE 3 - WOULD IT BREAK SOMETHING? A star here would leave some unit without room. */
  *ruleLookahead(grid, depth) {
    const status = this.units.map(unit => this.status(grid, unit));
    let found = false;
    for (let cell = 0; cell < this.n * this.n; cell++) {
      if (grid[cell] !== UNKNOWN) continue;
      const removed = new Set(this.neighbours[cell]);
      removed.add(cell);
      for (const u of this.unitsOf[cell]) {
        const [needed, open] = status[u];
        if (needed === 1) open.forEach(c => removed.add(c));
      }
      const affected = new Set();
      for (const x of removed) this.unitsOf[x].forEach(u => affected.add(u));
      for (const u of [...affected].sort((a, b) => a - b)) {
        const [needed, open] = status[u];
        if (needed <= 0) continue;
        const stillNeeded = needed - (this.unitsOf[cell].includes(u) ? 1 : 0);
        const remaining = open.filter(c => !removed.has(c));
        if (!this.canFit(remaining, stillNeeded)) {
          grid[cell] = BLANK;
          yield this.step('blank', [cell], `If ${this.name(cell)} had a star, ${this.units[u].name} would no longer have room for its stars. So it's crossed out.`, grid, depth);
          found = true;
          break;
        }
      }
    }
    return found ? 'progress' : 'stuck';
  }

  /** RULE 4 - FOLLOW THE WHAT-IF ALL THE WAY: a pretend star, then Rules 1-2 on a scratch copy. */
  *ruleDeepLookahead(grid, depth) {
    let found = false;
    for (let cell = 0; cell < this.n * this.n; cell++) {
      if (grid[cell] !== UNKNOWN) continue;
      const reason = this.tryStarQuietly(grid.slice(), cell);
      if (reason !== null) {
        grid[cell] = BLANK;
        const why = reason[0].toLowerCase() + reason.slice(1).replace(/\.+$/, '');
        yield this.step('blank', [cell], `Pretend ${this.name(cell)} has a star and follow the rules forward: it leads to a dead end (${why}). So it's crossed out.`, grid, depth);
        found = true;
      }
    }
    return found ? 'progress' : 'stuck';
  }

  /** Helper for Rule 4: returns the sentence explaining the dead end, or null. */
  tryStarQuietly(scratch, cell) {
    if (this.placeStar(scratch, cell) === null) return 'it would touch another star.';
    this.quiet = true;
    try {
      for (;;) {
        let progress = false;
        for (const rule of [this.ruleCounting, this.ruleSqueeze]) {
          const steps = rule.call(this, scratch, 0);
          let lastMessage = null, next = steps.next();
          while (!next.done) { lastMessage = next.value.message; next = steps.next(); }
          if (next.value === 'broken') return lastMessage;
          if (next.value === 'progress') { progress = true; break; }
        }
        if (!progress) return null;
      }
    } finally {
      this.quiet = false;
    }
  }

  /** Apply the rules, cheapest first, until all are stuck. Returns false if the board broke. */
  *deduce(grid, depth) {
    const rules = [this.ruleCounting, this.ruleSqueeze, this.ruleLookahead];
    if (this.deepLookahead) rules.push(this.ruleDeepLookahead);
    for (;;) {
      let progressed = false;
      for (const rule of rules) {
        const outcome = yield* rule.call(this, grid, depth);
        if (outcome === 'broken') return false;
        if (outcome === 'progress') { progressed = true; break; }
      }
      if (!progressed) return true;
    }
  }

  // ==========================================================================
  //  GUESSING
  // ==========================================================================

  /** The unit with the fewest ways left; within it, the cell whose star crosses out the most. */
  chooseGuess(grid) {
    let bestCell = null, bestScore = null;
    for (const unit of this.units) {
      const [needed, open] = this.status(grid, unit);
      if (needed <= 0 || !open.length) continue;
      const ways = comb(open.length, needed);
      for (const cell of open) {
        const impact = this.neighbours[cell].filter(nb => grid[nb] === UNKNOWN).length;
        const score = [ways, -impact];
        if (bestScore === null || lessThan(score, bestScore)) { bestScore = score; bestCell = cell; }
      }
    }
    return bestCell;
  }

  /** Logic, then (if stuck) a guess on a copy, then (if it fails) undo. Returns true when done. */
  *search(grid, depth, maxSolutions) {
    for (;;) {
      const stillPossible = yield* this.deduce(grid, depth);
      if (!stillPossible) return false;

      if (!grid.includes(UNKNOWN)) {
        this.solutions.push(this.snapshot(grid));
        yield this.step('solved', [], `Solved! Every row, column and region has exactly ${this.stars} star(s) and no stars touch.`, grid, depth);
        return this.solutions.length >= maxSolutions;
      }

      const cell = this.chooseGuess(grid);
      this.guesses++;
      const trial = grid.slice();
      this.placeStar(trial, cell);
      yield this.step('guess', [cell], `Stuck - trying a star at ${this.name(cell)} as a guess (guess level ${depth + 1}).`, trial, depth + 1);

      const done = yield* this.search(trial, depth + 1, maxSolutions);
      if (done) return true;

      this.backtracks++;
      grid[cell] = BLANK;
      yield this.step('backtrack', [cell], `Undoing the guess: a star at ${this.name(cell)} leads nowhere, so that cell must be blank.`, grid, depth);
    }
  }

  // ==========================================================================
  //  PUBLIC FUNCTIONS
  // ==========================================================================

  /** Solve, yielding a report after every action (the app animates these). */
  *solveSteps(maxSolutions = 1) {
    this.guesses = 0;
    this.backtracks = 0;
    this.solutions = [];
    const grid = new Array(this.n * this.n).fill(UNKNOWN);
    yield this.step('start', [], 'Starting with an empty board.', grid, 0);
    yield* this.search(grid, 0, maxSolutions);
    if (!this.solutions.length) {
      yield this.step('failed', [], 'This puzzle has no solution - please double-check the regions.', grid, 0);
    }
  }

  /** Solve without animation: rows of true (star) / false, or null if impossible. */
  solve() {
    for (const _ of this.solveSteps(1)) { /* run through every step */ }
    if (!this.solutions.length) return null;
    return this.solutions[0].map(row => row.map(cell => cell === STAR));
  }

  /** Count solutions, stopping at `limit`. A well-made puzzle has exactly 1. */
  countSolutions(limit = 2) {
    for (const _ of this.solveSteps(limit)) { /* run through every step */ }
    return this.solutions.length;
  }
}

function range(n) { return Array.from({ length: n }, (_, i) => i); }

/** Read a puzzle from text: one row per line, '#' lines are comments, spaces ignored. */
function parsePuzzle(text) {
  return text.split(/\r?\n/).map(line => line.trim())
    .filter(line => line && !line.startsWith('#'))
    .map(line => line.split(/\s+/).join(''));
}

/** Independently check a finished answer against all four rules. */
function checkSolution(regions, starsGrid, stars = 2) {
  const n = regions.length, starCells = [];
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (starsGrid[r][c]) starCells.push([r, c]);
  for (let i = 0; i < n; i++) {
    if (starCells.filter(([r]) => r === i).length !== stars) return false;
    if (starCells.filter(([, c]) => c === i).length !== stars) return false;
  }
  for (const label of new Set(regions.flatMap(row => [...row]))) {
    if (starCells.filter(([r, c]) => regions[r][c] === label).length !== stars) return false;
  }
  for (let i = 0; i < starCells.length; i++) {
    for (let j = i + 1; j < starCells.length; j++) {
      const [r1, c1] = starCells[i], [r2, c2] = starCells[j];
      if (Math.abs(r1 - r2) <= 1 && Math.abs(c1 - c2) <= 1) return false;
    }
  }
  return true;
}

// Let Node.js (used by the tests) load this file too; browsers just see the globals above.
if (typeof module !== 'undefined') {
  module.exports = { StarBattleSolver, UNKNOWN, STAR, BLANK, comb, parsePuzzle, checkSolution };
}
