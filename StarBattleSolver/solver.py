"""
================================================================================
 STAR BATTLE SOLVER  -  the "brain" of the program
================================================================================

WHAT IS A STAR BATTLE PUZZLE?
    You get a square grid (here 10 x 10) that is split up into 10 coloured
    "regions" (blobs of cells). Your job is to put stars in some of the cells
    so that:
        1. Every ROW has exactly 2 stars.
        2. Every COLUMN has exactly 2 stars.
        3. Every REGION has exactly 2 stars.
        4. No two stars TOUCH each other - not even corner-to-corner
           (diagonally).

HOW DOES THIS PROGRAM SOLVE IT?  (the short version)
    It solves the puzzle the same way a careful human would, plus one trick
    a human can't do quickly: perfect "what-if" guessing with an eraser.

    Every cell is always in one of three states:
        UNKNOWN - we haven't decided yet
        STAR    - we are sure a star goes here
        BLANK   - we are sure NO star goes here (a human would draw an "x")

    Step 1 - LOGIC. We keep applying four rules of thumb ("deductions")
             that turn UNKNOWN cells into STARs or BLANKs:
                 Rule 1  Counting      - is a row/column/region full, or
                                         does it have exactly enough room?
                 Rule 2  Squeeze       - do N regions fit inside N rows?
                 Rule 3  Quick what-if - would a star here instantly leave
                                         some row/column/region without room?
                 Rule 4  Deep what-if  - would a star here, after following
                                         Rules 1 & 2 forward, cause a problem?
             Each rule is explained in plain English further down.

    Step 2 - GUESS. When all four rules get stuck, we pick the cell where a
             guess will teach us the most, pretend it holds a star, and keep
             going with logic on a *copy* of the board.

    Step 3 - UNDO. If that pretend star eventually leads to something
             impossible (e.g. a row that can no longer fit its 2 stars), we
             throw the copy away ("backtrack"), and now we KNOW that cell
             must be BLANK - which is real progress. Then back to Step 1.

    Because the logic rules do most of the work, the program only needs a
    handful of guesses on a typical 10 x 10 puzzle, so it finishes in a
    fraction of a second.

HOW THE PICTURE (GUI) WATCHES THE SOLVER
    The solver is written as a Python "generator". In plain terms: every time
    it does something interesting (places a star, crosses cells out, makes a
    guess, undoes a guess) it PAUSES and hands back a little report called a
    `Step`. The GUI draws that report on screen, waits a moment, and then asks
    the solver to continue. That is how you get to watch it think in real
    time. Code that doesn't care about animation can simply call `solve()`.

You can also run this file on its own from a terminal:
    python solver.py puzzles/example_1_easy.txt
================================================================================
"""

# `dataclass` is a shortcut for making simple "record" objects that just hold
# a few named pieces of information (like a form with labelled boxes).
from dataclasses import dataclass, field
# `comb` counts combinations, e.g. comb(5, 2) = 10 ways to pick 2 things from 5.
from math import comb
import sys


# ------------------------------------------------------------------------------
# The three possible states of a cell. We use small numbers because computers
# compare numbers very quickly; the names just make the code readable.
# ------------------------------------------------------------------------------
UNKNOWN = 0   # not decided yet
STAR = 1      # definitely a star
BLANK = 2     # definitely NOT a star


@dataclass
class Step:
    """
    One "report" the solver hands back each time it does something.

    action  - a short word describing what happened. One of:
              "start"       : the empty board, before anything happens
              "star"        : one or more stars were placed by logic
              "blank"       : one or more cells were crossed out by logic
              "guess"       : the solver is trying a pretend star
              "backtrack"   : a guess failed and was erased
              "contradiction": the board just became impossible
              "solved"      : finished!
              "failed"      : the puzzle has no solution
    cells   - list of (row, column) cells this step changed or is about.
    message - a plain-English sentence explaining the step.
    grid    - a snapshot of the whole board right after this step, as a list
              of lists filled with UNKNOWN / STAR / BLANK.
    depth   - how many guesses deep we currently are (0 = pure logic, no
              guesses in play). Handy for showing "how unsure" the board is.
    """
    action: str
    cells: list
    message: str
    grid: list
    depth: int = 0


@dataclass
class _Unit:
    """
    A "unit" is any group of cells that must contain exactly 2 stars:
    a row, a column, or a region. Treating all three the same way means we
    only have to write each rule once instead of three times.
    """
    name: str                         # e.g. "row 3", "column 7", "region C"
    cells: list = field(default_factory=list)  # cell numbers in this group


class StarBattleSolver:
    """
    Holds one puzzle and knows how to solve it.

    INSIDE THE COMPUTER, a cell is just a single number from 0 to 99
    (for a 10 x 10 grid): number = row * 10 + column.
    So the top-left cell is 0, the cell to its right is 1, the first cell of
    the second row is 10, and the bottom-right cell is 99. This "flat"
    numbering makes copying the board fast (it's one simple list), which
    matters because guessing requires lots of copies.
    """

    def __init__(self, regions, stars=2, deep_lookahead=True):
        """
        regions - a list of rows, each row a list (or string) of region labels.
                  Example for a tiny 4 x 4 board:
                      ["AABB",
                       "AABB",
                       "CCDD",
                       "CCDD"]
                  Any labels work (letters, numbers, ...), as long as there are
                  exactly as many different labels as there are rows.
        stars   - how many stars go in each row / column / region (2 for the
                  standard 10 x 10 puzzle, 1 for small beginner puzzles).
        deep_lookahead - whether to use Rule 4 (see below). It makes the
                  solver need far fewer guesses, which is nicer to watch.
                  The puzzle generator switches it off because it solves
                  hundreds of throwaway puzzles and only cares about speed.
        """
        # ---- Basic size information --------------------------------------
        self.n = len(regions)          # number of rows (also = columns)
        self.stars = stars             # stars required per unit

        # Make sure the board really is square (same number of rows/columns).
        for row in regions:
            if len(row) != self.n:
                raise ValueError("The grid must be square: every row needs "
                                 f"exactly {self.n} cells.")

        # ---- Give every region label a simple number 0, 1, 2, ... --------
        # We sort the labels so "A" becomes region 0, "B" becomes region 1, etc.
        labels = sorted({label for row in regions for label in row}, key=str)
        if len(labels) != self.n:
            raise ValueError(f"A {self.n}x{self.n} puzzle needs exactly "
                             f"{self.n} regions, but {len(labels)} were found.")
        self.labels = labels
        label_to_number = {label: i for i, label in enumerate(labels)}
        # region_of[cell] tells us which region a cell belongs to.
        self.region_of = [label_to_number[regions[r][c]]
                          for r in range(self.n) for c in range(self.n)]

        # ---- Build the list of all "units" (rows, columns, regions) ------
        self.units = []
        for r in range(self.n):        # one unit per row
            self.units.append(_Unit(f"row {r + 1}",
                                    [r * self.n + c for c in range(self.n)]))
        for c in range(self.n):        # one unit per column
            self.units.append(_Unit(f"column {c + 1}",
                                    [r * self.n + c for r in range(self.n)]))
        for k, label in enumerate(labels):   # one unit per region
            cells = [i for i in range(self.n * self.n) if self.region_of[i] == k]
            self.units.append(_Unit(f"region {label}", cells))
        # Remember where the region units start in the list (after rows+cols).
        self.first_region_unit = 2 * self.n

        # units_of[cell] = the 3 units (its row, its column, its region) that
        # a cell belongs to. Pre-computing this saves time later.
        self.units_of = [[] for _ in range(self.n * self.n)]
        for u, unit in enumerate(self.units):
            for cell in unit.cells:
                self.units_of[cell].append(u)

        # neighbours[cell] = the up-to-8 cells touching it (including
        # diagonals). A star "poisons" all of these: none can hold a star.
        self.neighbours = []
        for cell in range(self.n * self.n):
            r, c = divmod(cell, self.n)   # divmod gives (row, column) at once
            touching = set()
            for dr in (-1, 0, 1):          # look one row up, same row, one down
                for dc in (-1, 0, 1):      # ...and one column left/same/right
                    if (dr, dc) == (0, 0):
                        continue           # skip the cell itself
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < self.n and 0 <= cc < self.n:   # stay on board
                        touching.add(rr * self.n + cc)
            self.neighbours.append(touching)

        self.deep_lookahead = deep_lookahead
        # True while Rule 4 runs a silent experiment (see _rule_deep_lookahead).
        self._quiet = False

        # Some statistics the GUI likes to show.
        self.guesses = 0
        self.backtracks = 0

    # ==========================================================================
    #  Small helper functions
    # ==========================================================================
    @staticmethod
    def _cap(text):
        """Capitalise only the first letter ('region I' -> 'Region I')."""
        return text[0].upper() + text[1:]

    def name(self, cell):
        """Turn a cell number into friendly text like 'row 3, column 5'."""
        r, c = divmod(cell, self.n)
        return f"row {r + 1}, column {c + 1}"

    def _rc(self, cells):
        """Turn cell numbers into (row, column) pairs for the GUI."""
        return [divmod(cell, self.n) for cell in cells]

    def _snapshot(self, grid):
        """Copy the flat board into a list of rows (what the GUI draws)."""
        return [grid[r * self.n:(r + 1) * self.n] for r in range(self.n)]

    def _step(self, action, cells, message, grid, depth):
        """Package up a report (a Step) for whoever is watching."""
        if self._quiet:
            # During a silent "what-if" experiment (Rule 4) nobody is
            # watching, so we skip the board snapshot to save time.
            return Step(action, [], message, None, depth)
        return Step(action, self._rc(cells), message, self._snapshot(grid), depth)

    def _can_fit(self, cells, needed):
        """
        Question: "Among these still-open cells, can I place `needed` stars so
        that none of them touch each other?"

        How: take the first open cell. Either a star goes there (then its
        neighbours are off-limits and we need one fewer star from the rest),
        or it doesn't (then we need all the stars from the rest). If either
        option works, the answer is yes.

        This sounds slow, but `needed` is never more than 2 in a normal
        puzzle, so it only ever looks at a few dozen combinations.
        """
        if needed <= 0:
            return True                        # nothing left to place: easy
        if len(cells) < needed:
            return False                       # not even enough cells
        first, rest = cells[0], cells[1:]
        touching = self.neighbours[first]
        # Option A: put a star on `first`, remove its neighbours, recurse.
        if self._can_fit([c for c in rest if c not in touching], needed - 1):
            return True
        # Option B: leave `first` empty and try with the remaining cells.
        return self._can_fit(rest, needed)

    def _place_star(self, grid, cell):
        """
        Put a star on `cell` and cross out (BLANK) every cell touching it,
        because stars may never touch. Returns the list of newly blanked cells,
        or None if this is impossible (a touching cell already has a star).
        """
        grid[cell] = STAR
        crossed = []
        for nb in self.neighbours[cell]:
            if grid[nb] == STAR:
                return None                    # two touching stars: illegal
            if grid[nb] == UNKNOWN:
                grid[nb] = BLANK
                crossed.append(nb)
        return crossed

    def _status(self, grid, unit):
        """
        For one unit, return (stars_needed, open_cells):
            stars_needed - how many MORE stars this row/column/region needs
            open_cells   - its cells that are still UNKNOWN
        """
        have = 0
        open_cells = []
        for cell in unit.cells:
            if grid[cell] == STAR:
                have += 1
            elif grid[cell] == UNKNOWN:
                open_cells.append(cell)
        return self.stars - have, open_cells

    # ==========================================================================
    #  THE LOGIC RULES ("deductions")
    #  Each rule looks at the board, and if it can prove something, it changes
    #  the board, reports what it did (with `yield`), and says "I made
    #  progress". If it finds the board is impossible it reports that instead.
    #
    #  Python note for beginners: a function containing `yield` is a
    #  "generator". `yield something` = "here's a report, pause me until
    #  someone asks for the next one". `return value` at the end hands a final
    #  answer back to whoever called it with `yield from`.
    # ==========================================================================

    def _rule_counting(self, grid, depth):
        """
        RULE 1 - "COUNTING"  (the bread-and-butter rule)

        For every row, column and region, compare how many stars it still
        needs with how many open cells it has left:

          a) FULL: It already has its 2 stars  ->  every other open cell in it
             must be blank.
          b) NO ROOM: It needs more stars than it can possibly fit (taking
             "no touching" into account)  ->  the board is impossible.
          c) EXACT FIT: The number of open cells equals the number of stars it
             still needs  ->  every one of those cells must be a star.

        Returns "progress", "stuck" (nothing to do) or "broken" (impossible).
        """
        for unit in self.units:
            needed, open_cells = self._status(grid, unit)

            if needed < 0:
                # More stars than allowed - can only happen after a bad guess.
                yield self._step("contradiction", [], f"{unit.name} has too many "
                                 "stars - this can't be right.", grid, depth)
                return "broken"

            if needed == 0 and open_cells:
                # (a) FULL: cross out everything else in this unit.
                for cell in open_cells:
                    grid[cell] = BLANK
                yield self._step("blank", open_cells,
                                 f"{self._cap(unit.name)} already has its "
                                 f"{self.stars} star(s), so the rest of it is "
                                 "crossed out.", grid, depth)
                return "progress"

            if needed > 0 and not self._can_fit(open_cells, needed):
                # (b) NO ROOM: this unit can never be completed.
                yield self._step("contradiction", open_cells,
                                 f"{self._cap(unit.name)} needs {needed} more "
                                 "star(s) but there's no room for them without "
                                 "stars touching.", grid, depth)
                return "broken"

            if needed > 0 and needed == len(open_cells):
                # (c) EXACT FIT: every open cell must hold a star.
                crossed = []
                for cell in open_cells:
                    result = self._place_star(grid, cell)
                    if result is None:
                        yield self._step("contradiction", [cell], "Two stars "
                                         f"would touch in {unit.name}.", grid, depth)
                        return "broken"
                    crossed += result
                yield self._step("star", open_cells,
                                 f"{self._cap(unit.name)} needs {needed} more "
                                 f"star(s) and has exactly {needed} open cell(s) "
                                 "left, so they all get stars (and their "
                                 "neighbours are crossed out).", grid, depth)
                return "progress"

        return "stuck"

    def _rule_squeeze(self, grid, depth):
        """
        RULE 2 - "SQUEEZE" (also called "pigeonhole")

        Picture a horizontal band of, say, 3 rows. Those 3 rows hold exactly
        3 x 2 = 6 stars in total.

          a) If 3 regions sit COMPLETELY inside that band, those 3 regions
             need 3 x 2 = 6 stars, all of which must come from the band.
             That uses up every star the band has! So any band cell belonging
             to a DIFFERENT region must be blank.
             (If 4 regions sat completely inside 3 rows, they'd need 8 stars
             but only 6 exist - impossible.)

          b) Flip it around: if only 3 regions TOUCH the band at all, then
             the band's 6 stars must all come from those 3 regions, which
             fills them up. So any cells of those regions OUTSIDE the band
             must be blank.

        We check every band of consecutive rows, and every band of
        consecutive columns, of every width. ("Open" here means not blank.)
        """
        n = self.n
        region_units = self.units[self.first_region_unit:]

        # We do the same check twice: once for rows, once for columns.
        #   line_of(cell)  -> which row (or column) number a cell is in
        #   line_cells[i]  -> all the cells in row (or column) number i
        for direction, line_of, line_cells in (
                ("rows", lambda cell: cell // n, self.units[:n]),
                ("columns", lambda cell: cell % n, self.units[n:2 * n])):

            # SPEED TRICK: for each region we record which lines it still has
            # open (non-blank) cells in, as a row of on/off switches packed
            # into one whole number (a "bitmask"). Switch number 3 is ON if
            # the region still has an open cell in line 3. Comparing two such
            # numbers takes the computer a single step, which is far quicker
            # than comparing two lists.
            masks = []
            for unit in region_units:
                mask = 0
                for cell in unit.cells:
                    if grid[cell] != BLANK:
                        mask |= 1 << line_of(cell)   # turn switch ON
                masks.append(mask)

            for start in range(n):                  # band's first line
                band_mask = 0
                for end in range(start, n - 1):     # band's last line
                    band_mask |= 1 << end           # add this line to band
                    width = end - start + 1         # number of lines in band

                    # Regions completely inside the band (no open cell
                    # outside it), and regions with any open cell in it.
                    inside = [k for k in range(n)
                              if masks[k] and not masks[k] & ~band_mask]
                    touching = [k for k in range(n) if masks[k] & band_mask]
                    if len(inside) < width < len(touching):
                        continue                    # nothing to learn here

                    band_text = (f"{direction} {start + 1}-{end + 1}" if width > 1
                                 else f"{direction[:-1]} {start + 1}")

                    if len(inside) > width:
                        # Too many regions squeezed into too few lines.
                        yield self._step("contradiction", [],
                                         f"{len(inside)} regions are squeezed into "
                                         f"just {band_text} - not enough stars "
                                         "to go round.", grid, depth)
                        return "broken"

                    if len(touching) < width:
                        # Too few regions to supply all the band's stars.
                        yield self._step("contradiction", [],
                                         f"Only {len(touching)} region(s) can "
                                         f"supply stars to {band_text}, which "
                                         "needs more than that.", grid, depth)
                        return "broken"

                    if len(inside) == width:
                        # (a) Cross out band cells from other regions.
                        to_blank = [cell
                                    for line in range(start, end + 1)
                                    for cell in line_cells[line].cells
                                    if grid[cell] == UNKNOWN
                                    and self.region_of[cell] not in inside]
                        if to_blank:
                            for cell in to_blank:
                                grid[cell] = BLANK
                            names = ", ".join(self.labels[k] for k in inside)
                            yield self._step("blank", to_blank,
                                             f"Squeeze: region(s) {names} fit "
                                             f"entirely inside {band_text}, so "
                                             "they use up all of its stars. "
                                             "Other cells there are crossed out.",
                                             grid, depth)
                            return "progress"

                    if len(touching) == width:
                        # (b) Cross out the touching regions' cells outside.
                        to_blank = [cell
                                    for k in touching
                                    for cell in region_units[k].cells
                                    if grid[cell] == UNKNOWN
                                    and not (1 << line_of(cell)) & band_mask]
                        if to_blank:
                            for cell in to_blank:
                                grid[cell] = BLANK
                            names = ", ".join(self.labels[k] for k in touching)
                            yield self._step("blank", to_blank,
                                             f"Squeeze: {band_text} can only get "
                                             f"stars from region(s) {names}, which "
                                             "fills those regions up. Their cells "
                                             "outside are crossed out.", grid, depth)
                            return "progress"
        return "stuck"

    def _rule_lookahead(self, grid, depth):
        """
        RULE 3 - "WOULD IT BREAK SOMETHING?"

        For each open cell, imagine putting a star there for a moment (we
        don't actually change the board). That star would:
            - cross out its 8 neighbours, and
            - if it finishes off its row/column/region, cross out the rest
              of that row/column/region too.
        Then we check every row, column and region: can each one still fit
        the stars it needs? If ANY of them couldn't, then a star in this cell
        would wreck the puzzle - so the cell must be blank.

        Human solvers do this all the time ("if I put a star here, column 4
        would have no room left...").
        """
        # Work out each unit's current status once, up front.
        status = [self._status(grid, unit) for unit in self.units]
        # Did we cross anything out during this pass?
        # (Crossing out a cell only ever makes the board MORE cramped, so a
        # conclusion we reach with the slightly older status is still true.
        # That lets us finish the whole pass instead of restarting each time.)
        found = False

        for cell in range(self.n * self.n):
            if grid[cell] != UNKNOWN:
                continue

            # Cells that would get crossed out by an imaginary star here.
            removed = set(self.neighbours[cell])
            removed.add(cell)   # the cell itself is "used up" by the star
            for u in self.units_of[cell]:
                needed, open_cells = status[u]
                if needed == 1:
                    # This star would complete the unit: rest becomes blank.
                    removed.update(open_cells)

            # Only rows/columns/regions that would lose open cells can be
            # harmed, so we only check those (much faster than checking all).
            affected = set()
            for x in removed:
                affected.update(self.units_of[x])

            for u in sorted(affected):
                needed, open_cells = status[u]
                if needed <= 0:
                    continue
                still_needed = needed - (1 if u in self.units_of[cell] else 0)
                remaining = [c for c in open_cells if c not in removed]
                if not self._can_fit(remaining, still_needed):
                    grid[cell] = BLANK
                    yield self._step("blank", [cell],
                                     f"If {self.name(cell)} had a star, "
                                     f"{self.units[u].name} "
                                     "would no longer have room for its stars. "
                                     "So it's crossed out.", grid, depth)
                    found = True
                    break          # this cell is settled; move to the next
        return "progress" if found else "stuck"

    def _rule_deep_lookahead(self, grid, depth):
        """
        RULE 4 - "FOLLOW THE WHAT-IF ALL THE WAY THROUGH"

        A stronger version of Rule 3. For each open cell we make a scratch
        copy of the board, put a pretend star in the cell, and then keep
        applying Rules 1 and 2 on the scratch copy, like a chain of dominoes.
        If the dominoes eventually knock over something impossible (a row
        with no room left, too many stars in a region, ...), the pretend star
        was wrong - so on the REAL board that cell gets crossed out.

        The scratch work is done silently (nothing is shown on screen); only
        the conclusion is reported. This is the rule that makes the solver
        need very few real guesses, even on hard puzzles.
        """
        found = False
        for cell in range(self.n * self.n):
            if grid[cell] != UNKNOWN:
                continue
            scratch = grid[:]                  # a throwaway copy
            reason = self._try_star_quietly(scratch, cell)
            if reason is not None:
                # As in Rule 3: crossing a cell out only makes things more
                # cramped, so we can keep scanning instead of restarting.
                grid[cell] = BLANK
                yield self._step("blank", [cell],
                                 f"Pretend {self.name(cell)} has a star and follow "
                                 f"the rules forward: it leads to a dead end "
                                 f"({reason[0].lower() + reason[1:].rstrip('.')})."
                                 " So it's crossed out.", grid, depth)
                found = True
        return "progress" if found else "stuck"

    def _try_star_quietly(self, scratch, cell):
        """
        Helper for Rule 4. Puts a star on `cell` in the scratch board, then
        repeats Rules 1 and 2 until they stop. Returns a sentence explaining
        the dead end if one is reached, or None if nothing went wrong.
        """
        if self._place_star(scratch, cell) is None:
            return "it would touch another star."
        self._quiet = True                     # don't make snapshots
        try:
            while True:
                progress = False
                for rule in (self._rule_counting, self._rule_squeeze):
                    # Run the rule, remembering the last message it gave.
                    steps = rule(scratch, 0)
                    last_message = None
                    try:
                        while True:
                            last_message = next(steps).message
                    except StopIteration as finished:
                        outcome = finished.value   # the rule's return value
                    if outcome == "broken":
                        return last_message
                    if outcome == "progress":
                        progress = True
                        break                  # back to Rule 1
                if not progress:
                    return None                # settled down, no dead end
        finally:
            self._quiet = False                # always switch snapshots back on

    def _deduce(self, grid, depth):
        """
        Keep applying the rules, cheapest first, until none of them can make
        any more progress. Whenever a rule makes progress we start again
        from Rule 1, because the cheap rule is often unlocked by the new info.

        Returns True if the board is still possible, False if it broke.
        """
        rules = [self._rule_counting, self._rule_squeeze, self._rule_lookahead]
        if self.deep_lookahead:
            rules.append(self._rule_deep_lookahead)
        while True:
            for rule in rules:
                outcome = yield from rule(grid, depth)
                if outcome == "broken":
                    return False
                if outcome == "progress":
                    break           # go back to Rule 1
            else:
                # The `else` of a `for` loop runs only if we never hit `break`,
                # i.e. every single rule said "stuck". Time to stop.
                return True

    # ==========================================================================
    #  GUESSING ("search" / "backtracking")
    # ==========================================================================
    def _choose_guess(self, grid):
        """
        Pick the cell where a guess is most likely to teach us something.

        1. Find the row/column/region with the FEWEST ways left to place its
           remaining stars (e.g. "needs 1 star, only 2 open cells" = just 2
           ways). Guessing there is like guessing on a 50/50 instead of a
           1-in-10: either we're right, or we find out fast that we're wrong.
        2. Within it, choose the cell whose star would cross out the most
           open neighbours - a guess with big consequences gets
           confirmed or disproved quickly.
        """
        best_cell, best_score = None, None
        for unit in self.units:
            needed, open_cells = self._status(grid, unit)
            if needed <= 0 or not open_cells:
                continue
            ways = comb(len(open_cells), needed)   # number of combinations
            for cell in open_cells:
                impact = sum(1 for nb in self.neighbours[cell] if grid[nb] == UNKNOWN)
                # Fewer ways is better; then bigger impact is better.
                score = (ways, -impact)
                if best_score is None or score < best_score:
                    best_score, best_cell = score, cell
        return best_cell

    def _search(self, grid, depth, max_solutions):
        """
        The main loop: logic -> (stuck?) guess -> (wrong?) undo -> logic...

        It's "recursive", meaning when it makes a guess it calls ITSELF on a
        copy of the board. Think of it like exploring a maze: at each fork you
        take a path; if it dead-ends you walk back to the fork and know not to
        take that path again.

        Returns True if we've found as many solutions as we were asked for.
        """
        while True:
            # ---- Step 1: apply logic as far as it goes -------------------
            still_possible = yield from self._deduce(grid, depth)
            if not still_possible:
                return False                   # this branch is a dead end

            # ---- Is the board finished? ----------------------------------
            if UNKNOWN not in grid:
                # Every cell decided and Rule 1 found no problems, so every
                # row/column/region has exactly the right number of stars.
                self.solutions.append(self._snapshot(grid))
                yield self._step("solved", [], "Solved! Every row, column and "
                                 f"region has exactly {self.stars} star(s) and "
                                 "no stars touch.", grid, depth)
                return len(self.solutions) >= max_solutions

            # ---- Step 2: logic is stuck, so make a guess ------------------
            cell = self._choose_guess(grid)
            self.guesses += 1
            trial = grid[:]                    # a COPY of the board to play on
            self._place_star(trial, cell)
            yield self._step("guess", [cell], f"Stuck - trying a star at "
                             f"{self.name(cell)} as a guess (guess level "
                             f"{depth + 1}).", trial, depth + 1)

            # Explore the guess. If it finished the job, we're done.
            done = yield from self._search(trial, depth + 1, max_solutions)
            if done:
                return True

            # ---- Step 3: the guess failed (or we're hunting for more
            # solutions). Either way, every possibility with a star here has
            # now been explored, so on the ORIGINAL board this cell is blank.
            self.backtracks += 1
            grid[cell] = BLANK
            yield self._step("backtrack", [cell], f"Undoing the guess: a star at "
                             f"{self.name(cell)} leads nowhere, so that cell must "
                             "be blank.", grid, depth)
            # ...and loop back to Step 1 with this new knowledge.

    # ==========================================================================
    #  PUBLIC FUNCTIONS - the ones other files are meant to use
    # ==========================================================================
    def solve_steps(self, max_solutions=1):
        """
        Solve the puzzle, yielding a `Step` report after every action.
        Used by the GUI so it can animate each step.

        max_solutions - stop after finding this many solutions. Use 2 to check
                        whether a puzzle has exactly one answer.
        """
        self.guesses = 0
        self.backtracks = 0
        self.solutions = []
        grid = [UNKNOWN] * (self.n * self.n)   # start with every cell unknown
        yield self._step("start", [], "Starting with an empty board.", grid, 0)
        yield from self._search(grid, 0, max_solutions)
        if not self.solutions:
            yield self._step("failed", [], "This puzzle has no solution - "
                             "please double-check the regions.", grid, 0)

    def solve(self):
        """
        Solve without animation. Returns the solution as a list of rows of
        True (star) / False (no star), or None if there is no solution.
        """
        for _ in self.solve_steps(max_solutions=1):
            pass                               # just run through every step
        if not self.solutions:
            return None
        return [[cell == STAR for cell in row] for row in self.solutions[0]]

    def count_solutions(self, limit=2):
        """
        Count solutions, stopping once `limit` are found. A well-made puzzle
        has exactly 1. Returns a number from 0 up to `limit`.
        """
        for _ in self.solve_steps(max_solutions=limit):
            pass
        return len(self.solutions)


# ==============================================================================
#  Reading puzzle files and checking answers
# ==============================================================================
def load_puzzle(path):
    """
    Read a puzzle from a text file. The file should have one line per row,
    with one letter (or other symbol) per cell telling which region it is in.
    Spaces are ignored, and lines starting with '#' are comments. Example:

        # my puzzle
        AAABBBBCCC
        ...

    Returns a list of strings, one per row.
    """
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue                        # skip blank & comment lines
            rows.append("".join(line.split()))  # remove any spaces
    return rows


def check_solution(regions, stars_grid, stars=2):
    """
    Independently double-check a finished answer against all 4 rules.
    `stars_grid` is a list of rows of True/False. Returns True if valid.
    (Used by the tests, and a nice safety net.)
    """
    n = len(regions)
    star_cells = [(r, c) for r in range(n) for c in range(n) if stars_grid[r][c]]
    # Rule 1 & 2: each row and each column has the right number of stars.
    for i in range(n):
        if sum(1 for r, c in star_cells if r == i) != stars:
            return False
        if sum(1 for r, c in star_cells if c == i) != stars:
            return False
    # Rule 3: each region has the right number of stars.
    for label in {ch for row in regions for ch in row}:
        if sum(1 for r, c in star_cells if regions[r][c] == label) != stars:
            return False
    # Rule 4: no two stars touch (including diagonally).
    for i, (r1, c1) in enumerate(star_cells):
        for r2, c2 in star_cells[i + 1:]:
            if abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1:
                return False
    return True


def print_solution(regions, solution):
    """Print the board in the terminal, showing stars as '*'."""
    for r, row in enumerate(regions):
        print(" ".join("*" if solution[r][c] else row[c].lower()
                       for c in range(len(row))))


# ------------------------------------------------------------------------------
# This block only runs when you start this file directly
# (e.g. `python solver.py puzzles/example_1_easy.txt`), not when the GUI imports it.
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import time
    if len(sys.argv) < 2:
        print("Usage: python solver.py <puzzle file> [stars per unit]")
        sys.exit(1)
    puzzle = load_puzzle(sys.argv[1])
    star_count = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    solver = StarBattleSolver(puzzle, star_count)
    started = time.perf_counter()
    answer = solver.solve()
    elapsed = time.perf_counter() - started
    if answer is None:
        print("No solution exists for this puzzle.")
    else:
        print_solution(puzzle, answer)
        print(f"\nSolved in {elapsed * 1000:.1f} ms using {solver.guesses} "
              f"guess(es) and {solver.backtracks} backtrack(s).")
