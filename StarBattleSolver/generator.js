/*
================================================================================
 RANDOM PUZZLE GENERATOR AND DIFFICULTY GRADER  (JavaScript, for the web app)
================================================================================
Making a puzzle is a translation of puzzle_generator.py (see that file for the
long explanation):
    1. Secretly place the stars (2 per row and column, none touching).
    2. Pair them up and connect each pair with a path: the seed of a region.
    3. Grow the regions until they cover the board.
    4. Ask the solver how many answers the puzzle has. If more than one, move
       a cell of an unwanted answer into a neighbouring region and ask again.

GRADING (new in the web app). A puzzle's difficulty is the WIDEST reasoning
it needs: how much of the board a person has to keep in mind at once. The
solver always tries its simplest rule first (see deduce() in solver.js), so
the hardest rule it ever uses on the way to the answer is the hardest one the
puzzle really needs. The rule names are the ones in Carson's instruction
manual for the Star Battles round of the 2022 Berkeley mini Math Tournament.

    Easy    One or two rows/columns/sections at a time: Completed Sections,
            Rude Roommates, Nosy Neighbors, and squeezes inside one row or
            column.
    Medium  Two or more lines together: chunking, or No More Space / Too
            Much Space across 2 or more rows or columns.
    Hard    A chain of what-ifs (Rule 5), but no guessing.
    Expert  Trial and error: even with every rule, the solver has to guess.
            (A contest like BmMT only uses puzzles that logic alone can solve,
            so these are beyond contest puzzles.)

Because the solver is deterministic (same puzzle, same steps), the grade of a
puzzle is always the same, and gradePuzzle() can check any puzzle, including
the examples. To make a puzzle of a chosen difficulty we generate puzzles and
keep the first one whose grade matches. Of 300 random puzzles, about 15% were
Easy, 20% Medium, 41% Hard and 24% Expert, so Easy takes the longest.
================================================================================
*/
'use strict';

// Browsers load solver.js first; Node.js (the tests) loads it here.
const Solver = typeof module !== 'undefined' && module.exports ? require('./solver.js').StarBattleSolver : StarBattleSolver;

const REGION_LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const DIFFICULTIES = ['easy', 'medium', 'hard', 'expert'];

/** A small random-number generator that can be given a seed (same seed, same puzzle). */
function makeRng(seed) {
  let a = seed === undefined || seed === null ? (Math.random() * 2 ** 32) >>> 0 : seed >>> 0;
  const random = () => {            // "mulberry32"
    a = (a + 0x6D2B79F5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  return {
    random,
    choice: list => list[Math.floor(random() * list.length)],
    shuffle: list => {
      for (let i = list.length - 1; i > 0; i--) {
        const j = Math.floor(random() * (i + 1));
        [list[i], list[j]] = [list[j], list[i]];
      }
      return list;
    },
  };
}

/** Step 1: `stars` stars in every row and column, none touching. */
function randomStarLayout(n, stars, rng) {
  for (;;) {
    const columnCount = new Array(n).fill(0), layout = [];
    let ok = true;
    for (let r = 0; r < n && ok; r++) {
      const choices = rng.shuffle([...Array(n).keys()].filter(c => columnCount[c] < stars &&
        layout.every(([pr, pc]) => !(pr === r - 1 && Math.abs(pc - c) <= 1))));
      const picked = [];
      for (const c of choices) {
        if (picked.every(p => Math.abs(c - p) > 1)) picked.push(c);
        if (picked.length === stars) break;
      }
      if (picked.length < stars) { ok = false; break; }
      for (const c of picked) { columnCount[c]++; layout.push([r, c]); }
    }
    if (ok) return layout;
  }
}

/** A random "staircase" path of cells from a to b. */
function pathBetween([r, c], [r2, c2], rng) {
  const path = [[r, c]];
  while (r !== r2 || c !== c2) {
    const moves = [];
    if (r !== r2) moves.push([r2 > r ? 1 : -1, 0]);
    if (c !== c2) moves.push([0, c2 > c ? 1 : -1]);
    const [dr, dc] = rng.choice(moves);
    r += dr; c += dc;
    path.push([r, c]);
  }
  return path;
}

/** Steps 2 and 3: turn the secret stars into regions. Returns rows of letters, or null. */
function growRegions(n, layout, stars, rng) {
  const owner = Array.from({ length: n }, () => new Array(n).fill(null));
  const key = ([r, c]) => r * n + c, starSet = new Set(layout.map(key));
  const starsLeft = rng.shuffle(layout.slice());

  const freePath = (a, b) => {
    for (let i = 0; i < 8; i++) {
      const path = pathBetween(a, b, rng);
      if (path.every(([r, c]) => owner[r][c] === null &&
          (!starSet.has(r * n + c) || key(a) === r * n + c || key(b) === r * n + c))) return path;
    }
    return null;
  };

  for (let region = 0; region < n; region++) {
    const group = [starsLeft.pop()];
    let cells = [group[0]];
    for (let s = 0; s < stars - 1; s++) {
      const last = group[group.length - 1];
      const nearby = starsLeft.slice()
        .sort((x, y) => (Math.abs(x[0] - last[0]) + Math.abs(x[1] - last[1])) - (Math.abs(y[0] - last[0]) + Math.abs(y[1] - last[1])))
        .slice(0, 4);
      let partner = null, path = null;
      for (const p of nearby) { path = freePath(last, p); if (path) { partner = p; break; } }
      if (!partner) return null;
      starsLeft.splice(starsLeft.indexOf(partner), 1);
      group.push(partner);
      cells = cells.concat(path);
    }
    for (const [r, c] of cells) owner[r][c] = region;
  }

  let empty = owner.flat().filter(x => x === null).length;
  while (empty) {
    const frontier = [];
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        if (owner[r][c] !== null) continue;
        for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
          const rr = r + dr, cc = c + dc;
          if (rr >= 0 && rr < n && cc >= 0 && cc < n && owner[rr][cc] !== null) frontier.push([r, c, owner[rr][cc]]);
        }
      }
    }
    const [r, c, k] = rng.choice(frontier);
    owner[r][c] = k;
    empty--;
  }
  return owner.map(row => row.map(k => REGION_LETTERS[k]).join(''));
}

/** Would region k still be one connected blob without `removed`? */
function stillConnected(owner, k, [rr0, cc0]) {
  const n = owner.length, cells = new Set();
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (owner[r][c] === k && !(r === rr0 && c === cc0)) cells.add(r * n + c);
  if (!cells.size) return false;
  const start = cells.values().next().value, seen = new Set([start]), todo = [start];
  while (todo.length) {
    const cell = todo.pop(), r = Math.floor(cell / n), c = cell % n;
    for (const [nr, nc] of [[r + 1, c], [r - 1, c], [r, c + 1], [r, c - 1]]) {
      const nb = nr * n + nc;
      if (nr >= 0 && nr < n && nc >= 0 && nc < n && cells.has(nb) && !seen.has(nb)) { seen.add(nb); todo.push(nb); }
    }
  }
  return seen.size === cells.size;
}

/** Steps 4 and 5: tidy regions until our secret answer is the only one. */
function makeUnique(regions, secret, stars, rng, maxRounds = 60) {
  const n = regions.length;
  const owner = regions.map(row => [...row].map(ch => REGION_LETTERS.indexOf(ch)));
  const secretKeys = new Set(secret.map(([r, c]) => r * n + c));
  for (let round = 0; round < maxRounds; round++) {
    const current = owner.map(row => row.map(k => REGION_LETTERS[k]).join(''));
    const solver = new Solver(current, stars, false, false);   // Rules 4 and 5 off: faster
    if (solver.countSolutions(2) === 1) return current;
    let unwanted = null;
    for (const sol of solver.solutions) {
      const keys = [];
      sol.forEach((row, r) => row.forEach((v, c) => { if (v === 1) keys.push(r * n + c); }));
      if (keys.length !== secretKeys.size || keys.some(x => !secretKeys.has(x))) { unwanted = keys; break; }
    }
    if (!unwanted) return null;
    const candidates = rng.shuffle(unwanted.filter(x => !secretKeys.has(x)));
    let moved = false;
    for (const cell of candidates) {
      const r = Math.floor(cell / n), c = cell % n, old = owner[r][c];
      const options = new Set();
      for (const [rr, cc] of [[r + 1, c], [r - 1, c], [r, c + 1], [r, c - 1]]) {
        if (rr >= 0 && rr < n && cc >= 0 && cc < n && owner[rr][cc] !== old) options.add(owner[rr][cc]);
      }
      if (options.size && stillConnected(owner, old, [r, c])) {
        owner[r][c] = rng.choice([...options].sort((a, b) => a - b));
        moved = true;
        break;
      }
    }
    if (!moved) return null;
  }
  return null;
}

/** One random puzzle with exactly one solution, as rows of letters. */
function generatePuzzle(n = 10, stars = 2, rng = makeRng(), maxAttempts = 200) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const layout = randomStarLayout(n, stars, rng);
    const regions = growRegions(n, layout, stars, rng);
    if (!regions) continue;
    const result = makeUnique(regions, layout, stars, rng);
    if (result) return result;
  }
  throw new Error("Couldn't find a puzzle with a unique solution - try again.");
}

// How much of the board each rule asks you to keep in mind at once (see GRADING above).
const RULE_LEVEL = { counting: 1, roommates: 1, neighbors: 2, 'squeeze-1': 2, 'squeeze-2': 3, 'squeeze-wide': 3, chunking: 3, deep: 4 };
const LEVEL_NAME = { 1: 'easy', 2: 'easy', 3: 'medium', 4: 'hard', 5: 'expert' };

/**
 * Grade a puzzle by solving it once and watching what the solver needed.
 * Returns { difficulty, hardestRule, solutions, guesses, maxGuessLevel, steps }.
 * difficulty is null if the puzzle has no solution or more than one.
 */
function gradePuzzle(rows, stars = 2) {
  const solver = new Solver(rows, stars);
  let maxGuessLevel = 0, steps = 0, level = 1, hardestRule = 'counting';
  for (const step of solver.solveSteps()) {
    steps++;
    maxGuessLevel = Math.max(maxGuessLevel, step.depth);
    // Only the main line counts: steps inside a guess are part of trial and error.
    if (step.depth === 0 && RULE_LEVEL[step.rule] > level) { level = RULE_LEVEL[step.rule]; hardestRule = step.rule; }
  }
  if (maxGuessLevel > 0) { level = 5; hardestRule = 'guess'; }
  const solutions = new Solver(rows, stars, false).countSolutions(2);
  const difficulty = solutions === 1 ? LEVEL_NAME[level] : null;
  return { difficulty, hardestRule, solutions, guesses: solver.guesses, maxGuessLevel, steps };
}

/**
 * Keep generating until a puzzle of the wanted difficulty turns up.
 * onTry(tries) is called after every candidate (the app shows progress with it).
 */
function generateWithDifficulty(difficulty, { n = 10, stars = 2, seed, maxTries = 400, onTry } = {}) {
  if (!DIFFICULTIES.includes(difficulty)) throw new Error(`Unknown difficulty: ${difficulty}`);
  const rng = makeRng(seed);
  for (let tries = 1; tries <= maxTries; tries++) {
    const rows = generatePuzzle(n, stars, rng);
    const grade = gradePuzzle(rows, stars);
    if (onTry) onTry(tries, grade);
    if (grade.difficulty === difficulty) return { rows, grade, tries };
  }
  throw new Error(`No ${difficulty} puzzle turned up in ${maxTries} tries - please try again.`);
}

if (typeof module !== 'undefined') {
  module.exports = { makeRng, generatePuzzle, gradePuzzle, generateWithDifficulty, DIFFICULTIES };
}
