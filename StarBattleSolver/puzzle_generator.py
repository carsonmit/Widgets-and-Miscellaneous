"""
================================================================================
 RANDOM PUZZLE GENERATOR
================================================================================
Makes brand-new 10 x 10 Star Battle puzzles that have exactly ONE solution.

THE IDEA (in plain English)
    1. Secretly place 20 stars that obey the rules (2 per row, 2 per column,
       none touching). This will be the answer.
    2. Pair the stars up into 10 pairs. Each pair becomes the "seed" of one
       region: draw a little path of cells connecting the two stars of a pair.
    3. Grow the 10 regions outward, one random cell at a time, until every
       cell on the board belongs to some region. Now every region contains
       exactly 2 stars - so our secret answer is guaranteed to be valid.
    4. Ask the solver: "how many answers does this puzzle have?" If it's
       exactly 1, we're done.
    5. If there's a second, unwanted answer, find a cell that is a star in
       the unwanted answer but NOT in our secret answer, and hand that cell
       over to a neighbouring region. Our secret answer is unaffected (that
       cell has no star in it), but the unwanted answer now has 3 stars in
       one region and 1 in another, so it's no longer valid. Go back to 4.
       After a few rounds of this "tidying", only our answer is left.

    Usually takes about a second.

Run it from a terminal to print a new puzzle:
    python puzzle_generator.py
================================================================================
"""

import random
from solver import StarBattleSolver

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _random_star_layout(n, stars, rng):
    """
    Step 1: place `stars` stars in every row and column with none touching.
    We fill the board row by row, picking random columns, and if we paint
    ourselves into a corner we simply start over (this is fast for 10 x 10).
    """
    while True:
        column_count = [0] * n          # stars placed in each column so far
        layout = []                     # list of (row, col) star positions
        ok = True
        for r in range(n):
            # Columns that still need stars and don't touch last row's stars.
            choices = [c for c in range(n) if column_count[c] < stars and
                       all(not (pr == r - 1 and abs(pc - c) <= 1)
                           for pr, pc in layout)]
            rng.shuffle(choices)
            picked = []
            for c in choices:            # pick non-adjacent columns in this row
                if all(abs(c - p) > 1 for p in picked):
                    picked.append(c)
                if len(picked) == stars:
                    break
            if len(picked) < stars:
                ok = False               # dead end - restart from scratch
                break
            for c in picked:
                column_count[c] += 1
                layout.append((r, c))
        if ok:
            return layout


def _path_between(a, b, rng):
    """
    Cells along a simple random "staircase" path from cell a to cell b
    (moving one step up/down/left/right at a time).
    """
    (r, c), (r2, c2) = a, b
    path = [(r, c)]
    while (r, c) != (r2, c2):
        moves = []
        if r != r2:
            moves.append((1 if r2 > r else -1, 0))
        if c != c2:
            moves.append((0, 1 if c2 > c else -1))
        dr, dc = rng.choice(moves)
        r, c = r + dr, c + dc
        path.append((r, c))
    return path


def _grow_regions(n, layout, stars, rng):
    """
    Steps 2 and 3: turn the secret stars into regions.
    Returns a list of strings (the region map), or None if this attempt
    didn't work out (e.g. two seed paths crossed a third region's star).
    """
    owner = [[None] * n for _ in range(n)]   # which region owns each cell
    star_set = set(layout)
    stars_left = list(layout)
    rng.shuffle(stars_left)

    def free_path(a, b):
        """Try a few random paths from star a to star b; return the first one
        that doesn't run through another region or another star."""
        for _ in range(8):
            path = _path_between(a, b, rng)
            if all(owner[r][c] is None and ((r, c) not in star_set or (r, c) in (a, b))
                   for r, c in path):
                return path
        return None

    # --- Step 2: group the stars and connect each group with a path ---
    for region in range(n):
        group = [stars_left.pop()]
        cells = [group[0]]
        for _ in range(stars - 1):
            # Try the nearest few stars first, so regions stay compact.
            nearby = sorted(stars_left, key=lambda s: abs(s[0] - group[-1][0]) +
                            abs(s[1] - group[-1][1]))[:4]
            for partner in nearby:
                path = free_path(group[-1], partner)
                if path:
                    break
            else:
                return None                  # no partner reachable: give up
            stars_left.remove(partner)
            group.append(partner)
            cells += path
        for (r, c) in cells:
            owner[r][c] = region

    # --- Step 3: grow regions into empty neighbouring cells at random ---
    empty = sum(row.count(None) for row in owner)
    while empty:
        # Find every (empty cell, neighbouring region) pair and pick one.
        frontier = []
        for r in range(n):
            for c in range(n):
                if owner[r][c] is None:
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < n and 0 <= cc < n and owner[rr][cc] is not None:
                            frontier.append((r, c, owner[rr][cc]))
        r, c, k = rng.choice(frontier)
        owner[r][c] = k
        empty -= 1
    return ["".join(LETTERS[k] for k in row) for row in owner]


def _still_connected(owner, k, removed_cell):
    """
    Would region k still be one connected blob if `removed_cell` were taken
    away from it? We "flood fill" from any one of its cells (like pouring
    paint) and check whether the paint reaches all of the region's cells.
    """
    n = len(owner)
    cells = {(r, c) for r in range(n) for c in range(n)
             if owner[r][c] == k and (r, c) != removed_cell}
    if not cells:
        return False
    start = next(iter(cells))
    seen, todo = {start}, [start]
    while todo:
        r, c = todo.pop()
        for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if nb in cells and nb not in seen:
                seen.add(nb)
                todo.append(nb)
    return len(seen) == len(cells)


def _make_unique(regions, secret, stars, rng, max_rounds=60):
    """
    Steps 4 and 5: keep tidying regions until the puzzle has exactly one
    solution (our secret one). Returns the region map, or None if it gets
    stuck (then the caller just starts over with a fresh random board).
    """
    n = len(regions)
    owner = [[LETTERS.index(ch) for ch in row] for row in regions]
    for _ in range(max_rounds):
        current = ["".join(LETTERS[k] for k in row) for row in owner]
        # deep_lookahead=False: faster for the many quick checks we do here.
        solver = StarBattleSolver(current, stars, deep_lookahead=False)
        if solver.count_solutions(limit=2) == 1:
            return current                       # unique - finished!
        # Find an answer that isn't our secret one.
        unwanted = None
        for sol in solver.solutions:
            sol_stars = {(r, c) for r in range(n) for c in range(n) if sol[r][c] == 1}
            if sol_stars != secret:
                unwanted = sol_stars
                break
        # Cells with a star in the unwanted answer but not in ours.
        candidates = list(unwanted - secret)
        rng.shuffle(candidates)
        moved = False
        for (r, c) in candidates:
            old = owner[r][c]
            # Neighbouring regions this cell could join.
            options = {owner[rr][cc] for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1))
                       if 0 <= rr < n and 0 <= cc < n and owner[rr][cc] != old}
            if options and _still_connected(owner, old, (r, c)):
                owner[r][c] = rng.choice(sorted(options))
                moved = True
                break
        if not moved:
            return None
    return None


def generate_puzzle(n=10, stars=2, seed=None, max_attempts=200):
    """
    Keep generating candidates until one has exactly one solution.
    `seed` makes the result repeatable (same seed -> same puzzle).
    Returns the region map as a list of strings.
    """
    rng = random.Random(seed)
    for _ in range(max_attempts):
        layout = _random_star_layout(n, stars, rng)
        regions = _grow_regions(n, layout, stars, rng)
        if regions is None:
            continue
        result = _make_unique(regions, set(layout), stars, rng)
        if result is not None:
            return result
    raise RuntimeError("Couldn't find a puzzle with a unique solution - try again.")


if __name__ == "__main__":
    for line in generate_puzzle():
        print(line)
