"""
================================================================================
 STAR BATTLE SOLVER  -  the window you click on (the "GUI")
================================================================================
Start the program by running this file:
    python star_battle_gui.py

WHAT YOU CAN DO
    * Pick a region colour on the right, then click or drag on the grid to
      paint cells into that region. Right-click (or drag) erases.
      Shortcut: number keys 1-9 and 0 pick regions A-J.
    * Or load a ready-made example, open a puzzle file, or make a random one.
    * Press "Solve" and watch the solver work: stars appear, cells get
      crossed out, guesses are tried and undone. Every step is explained in
      plain English in the log at the bottom.
    * Pause, go one step at a time, change the speed, or jump to the end.

HOW IT WORKS (big picture)
    This file is only in charge of drawing things and reacting to clicks.
    All the puzzle-solving thinking lives in solver.py. The solver hands us
    one "Step" at a time (see solver.py for details); we draw each one, wait
    a little (based on the speed slider), then ask for the next one.

    The window is built with "tkinter", the toolkit that comes free with
    Python, so there is nothing extra to install.
================================================================================
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from solver import StarBattleSolver, load_puzzle, STAR, BLANK
from puzzle_generator import generate_puzzle

# ------------------------------------------------------------------------------
#  Settings you can tweak
# ------------------------------------------------------------------------------
SIZE = 10            # the grid is 10 x 10
CELL = 52            # how many pixels wide each cell is drawn
MARGIN = 12          # empty space around the grid, in pixels
LETTERS = "ABCDEFGHIJ"

# One soft colour per region (A to J). Written as "#RRGGBB" colour codes.
REGION_COLOURS = [
    "#f4a6a6",  # A - red
    "#f7c98b",  # B - orange
    "#f5ec8e",  # C - yellow
    "#b8e6a0",  # D - green
    "#9fdcd3",  # E - teal
    "#a9c8f2",  # F - blue
    "#c6b3ef",  # G - purple
    "#f0b4dc",  # H - pink
    "#d4c4a8",  # I - tan
    "#c9ced6",  # J - grey
]
UNPAINTED = "#ffffff"          # colour of cells not yet given a region

# Where the example puzzles live (a folder next to this file).
PUZZLE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "puzzles")

# Colours used in the step-by-step log for different kinds of steps.
LOG_COLOURS = {
    "star": "#1b5e20", "blank": "#555555", "guess": "#e65100",
    "backtrack": "#b71c1c", "contradiction": "#b71c1c",
    "solved": "#1b5e20", "failed": "#b71c1c", "start": "#000000",
}


class StarBattleApp:
    """Everything about the window lives inside this one object."""

    def __init__(self, root):
        self.root = root
        root.title("Star Battle Solver")

        # ---- The puzzle being edited ----------------------------------------
        # regions[row][col] holds a number 0-9 (region A-J), or None if that
        # cell hasn't been painted yet.
        self.regions = [[None] * SIZE for _ in range(SIZE)]
        self.current_region = 0          # the colour currently selected

        # ---- What the solver is showing -------------------------------------
        self.marks = None                # latest board snapshot from solver
        self.highlight = []              # cells changed in the latest step
        self.highlight_kind = None       # what kind of step that was
        self.steps = None                # the solver's step-by-step generator
        self.solver = None
        self.running = False             # True while animation is playing
        self.after_id = None             # the timer for the next step
        self.step_count = 0

        self._build_layout()
        self._load_first_example()
        self.redraw()

    # ==========================================================================
    #  Building the window
    # ==========================================================================
    def _build_layout(self):
        """Create all the buttons, labels and the drawing area."""
        side = SIZE * CELL + 2 * MARGIN

        # ---- Left: the grid itself (a "Canvas" is a blank drawing area) -----
        self.canvas = tk.Canvas(self.root, width=side, height=side,
                                bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=8, pady=8, sticky="n")
        # Tell the canvas what to do when the mouse is used on it.
        self.canvas.bind("<Button-1>", lambda e: self._paint(e, erase=False))
        self.canvas.bind("<B1-Motion>", lambda e: self._paint(e, erase=False))
        self.canvas.bind("<Button-3>", lambda e: self._paint(e, erase=True))
        self.canvas.bind("<B3-Motion>", lambda e: self._paint(e, erase=True))
        self.canvas.bind("<Button-2>", lambda e: self._paint(e, erase=True))  # Mac
        # Number keys 1..9 and 0 choose regions A..J.
        for i, key in enumerate("1234567890"):
            self.root.bind(key, lambda e, k=i: self._select_region(k))

        # ---- Right: the control panel ---------------------------------------
        panel = tk.Frame(self.root)
        panel.grid(row=0, column=1, padx=8, pady=8, sticky="n")

        # Region palette: one coloured button per region.
        tk.Label(panel, text="1. Paint the regions",
                 font=("Helvetica", 12, "bold")).pack(anchor="w")
        tk.Label(panel, text="Pick a colour, then click/drag on the grid.\n"
                 "Right-click erases. Keys 1-9, 0 pick A-J.",
                 justify="left", fg="#555").pack(anchor="w")
        palette = tk.Frame(panel)
        palette.pack(anchor="w", pady=4)
        self.palette_buttons = []
        for k in range(SIZE):
            b = tk.Button(palette, text=LETTERS[k], width=3, bg=REGION_COLOURS[k],
                          activebackground=REGION_COLOURS[k],
                          command=lambda k=k: self._select_region(k))
            b.grid(row=k // 5, column=k % 5, padx=2, pady=2)
            self.palette_buttons.append(b)

        # Puzzle file buttons.
        files = tk.Frame(panel)
        files.pack(anchor="w", pady=(6, 0), fill="x")
        self.example_var = tk.StringVar(value="Load example...")
        examples = self._example_names() or ["(no examples found)"]
        self.example_menu = tk.OptionMenu(files, self.example_var, *examples,
                                          command=self._load_example)
        self.example_menu.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.random_button = tk.Button(files, text="Random puzzle",
                                       command=self._random_puzzle)
        self.random_button.grid(row=1, column=0, sticky="ew")
        tk.Button(files, text="Clear grid", command=self._clear_regions
                  ).grid(row=1, column=1, sticky="ew")
        tk.Button(files, text="Open file...", command=self._open_file
                  ).grid(row=2, column=0, sticky="ew")
        tk.Button(files, text="Save file...", command=self._save_file
                  ).grid(row=2, column=1, sticky="ew")
        files.columnconfigure(0, weight=1)
        files.columnconfigure(1, weight=1)

        # Stars-per-unit option (2 is the standard for 10 x 10).
        stars_row = tk.Frame(panel)
        stars_row.pack(anchor="w", pady=(8, 0))
        tk.Label(stars_row, text="Stars per row/column/region:").pack(side="left")
        self.stars_var = tk.IntVar(value=2)
        tk.OptionMenu(stars_row, self.stars_var, 1, 2).pack(side="left")

        # Solving controls.
        tk.Label(panel, text="2. Watch it solve",
                 font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(14, 0))
        controls = tk.Frame(panel)
        controls.pack(anchor="w", fill="x")
        self.solve_button = tk.Button(controls, text="Solve", width=9,
                                      command=self._solve_or_pause)
        self.solve_button.grid(row=0, column=0, sticky="ew")
        tk.Button(controls, text="One step", command=self._single_step
                  ).grid(row=0, column=1, sticky="ew")
        tk.Button(controls, text="Skip to end", command=self._finish_now
                  ).grid(row=1, column=0, sticky="ew")
        tk.Button(controls, text="Reset", command=self._reset_solver
                  ).grid(row=1, column=1, sticky="ew")
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        # Speed slider: how long to wait between steps (in milliseconds).
        tk.Label(panel, text="Delay between steps (ms):").pack(anchor="w", pady=(8, 0))
        self.speed = tk.Scale(panel, from_=0, to=1500, orient="horizontal",
                              length=230, resolution=10)
        self.speed.set(300)
        self.speed.pack(anchor="w")

        # Statistics and the current status message.
        self.stats_label = tk.Label(panel, text="", justify="left",
                                    font=("Courier", 11))
        self.stats_label.pack(anchor="w", pady=(8, 0))
        self.status = tk.Label(panel, text="", wraplength=250, justify="left",
                               fg="#0d47a1")
        self.status.pack(anchor="w", pady=(6, 0))

        # Legend explaining the symbols.
        tk.Label(panel, text="Legend:  ★ star   × no star\n"
                 "yellow box = just changed\norange box = current guess",
                 justify="left", fg="#555").pack(anchor="w", pady=(10, 0))

        # ---- Bottom: the step-by-step log -----------------------------------
        log_frame = tk.Frame(self.root)
        log_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=8, pady=(0, 8))
        self.log = tk.Text(log_frame, height=9, wrap="word", state="disabled",
                           font=("Helvetica", 10))
        scroll = tk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for kind, colour in LOG_COLOURS.items():
            self.log.tag_configure(kind, foreground=colour)
        # Let the log grow if the window is resized.
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)

        self._select_region(0)
        self._update_stats()

    # ==========================================================================
    #  Drawing the grid
    # ==========================================================================
    def redraw(self):
        """
        Wipe the canvas and draw everything again from scratch:
        coloured cells, thin grid lines, thick region borders, then the
        stars and crosses, then highlight boxes.
        (Redrawing 100 cells takes a computer about a millisecond, so this
        simple approach is plenty fast.)
        """
        c = self.canvas
        c.delete("all")

        def corner(row, col):
            """Pixel position of the top-left corner of a cell."""
            return MARGIN + col * CELL, MARGIN + row * CELL

        # 1) Fill every cell with its region colour.
        for r in range(SIZE):
            for col in range(SIZE):
                x, y = corner(r, col)
                k = self.regions[r][col]
                fill = UNPAINTED if k is None else REGION_COLOURS[k]
                c.create_rectangle(x, y, x + CELL, y + CELL, fill=fill,
                                   outline="#bbbbbb")

        # 2) Thick lines wherever two neighbouring cells are in different
        #    regions - this is how region shapes are shown in printed puzzles.
        for r in range(SIZE):
            for col in range(SIZE):
                x, y = corner(r, col)
                if col + 1 < SIZE and self.regions[r][col] != self.regions[r][col + 1]:
                    c.create_line(x + CELL, y, x + CELL, y + CELL, width=3)
                if r + 1 < SIZE and self.regions[r][col] != self.regions[r + 1][col]:
                    c.create_line(x, y + CELL, x + CELL, y + CELL, width=3)
        # Outer border.
        c.create_rectangle(MARGIN, MARGIN, MARGIN + SIZE * CELL,
                           MARGIN + SIZE * CELL, width=4)

        # 3) Stars and crosses from the solver's latest snapshot.
        if self.marks is not None:
            for r in range(SIZE):
                for col in range(SIZE):
                    x, y = corner(r, col)
                    cx, cy = x + CELL / 2, y + CELL / 2   # centre of the cell
                    if self.marks[r][col] == STAR:
                        c.create_text(cx, cy, text="★", fill="#202020",
                                      font=("Helvetica", int(CELL * 0.55)))
                    elif self.marks[r][col] == BLANK:
                        c.create_text(cx, cy, text="×", fill="#777777",
                                      font=("Helvetica", int(CELL * 0.35)))

        # 4) Highlight the cells that the latest step touched.
        colour = "#ff8f00" if self.highlight_kind == "guess" else "#ffd600"
        if self.highlight_kind in ("backtrack", "contradiction"):
            colour = "#d50000"
        for r, col in self.highlight:
            x, y = corner(r, col)
            c.create_rectangle(x + 3, y + 3, x + CELL - 3, y + CELL - 3,
                               outline=colour, width=3)

    # ==========================================================================
    #  Editing regions
    # ==========================================================================
    def _select_region(self, k):
        """Remember which colour is selected and show it as pressed in."""
        self.current_region = k
        for i, b in enumerate(self.palette_buttons):
            b.configure(relief="sunken" if i == k else "raised",
                        bd=4 if i == k else 2)

    def _paint(self, event, erase):
        """Paint (or erase) the cell under the mouse pointer."""
        if self.steps is not None or self.marks is not None:
            # Changing the puzzle mid-solve (or after solving) would leave
            # stale stars on screen, so editing resets the solver first.
            if self.running:
                return
            self._reset_solver()
        # Convert the mouse's pixel position into a row and column number.
        col = int((event.x - MARGIN) // CELL)
        row = int((event.y - MARGIN) // CELL)
        if not (0 <= row < SIZE and 0 <= col < SIZE):
            return                           # clicked outside the grid
        new_value = None if erase else self.current_region
        if self.regions[row][col] != new_value:
            self.regions[row][col] = new_value
            self.redraw()

    def _clear_regions(self):
        self._reset_solver()
        self.regions = [[None] * SIZE for _ in range(SIZE)]
        self.redraw()
        self._set_status("Grid cleared. Paint your regions.")

    def _set_regions_from_rows(self, rows):
        """
        Fill the grid from a list of text rows like "AABBBCCDDD". Any 10
        different symbols are accepted; they get mapped onto colours A-J in
        alphabetical order.
        """
        if len(rows) != SIZE or any(len(r) != SIZE for r in rows):
            raise ValueError(f"The puzzle must be {SIZE} rows of {SIZE} cells.")
        symbols = sorted({ch for r in rows for ch in r})
        if len(symbols) > SIZE:
            raise ValueError(f"The puzzle uses {len(symbols)} different region "
                             f"symbols - at most {SIZE} are allowed.")
        index = {s: i for i, s in enumerate(symbols)}
        self._reset_solver()
        self.regions = [[index[ch] for ch in r] for r in rows]
        self.redraw()

    # ==========================================================================
    #  Loading / saving puzzles
    # ==========================================================================
    def _example_names(self):
        """List the example puzzle files in the puzzles folder."""
        if not os.path.isdir(PUZZLE_FOLDER):
            return []
        return sorted(f for f in os.listdir(PUZZLE_FOLDER) if f.endswith(".txt"))

    def _load_example(self, name):
        path = os.path.join(PUZZLE_FOLDER, name)
        if os.path.isfile(path):
            self._load_path(path)
        self.example_var.set("Load example...")

    def _load_first_example(self):
        """Start the program with the first example already on the board."""
        names = self._example_names()
        if names:
            self._load_path(os.path.join(PUZZLE_FOLDER, names[0]))
        else:
            self._set_status("Paint your regions, then press Solve.")

    def _load_path(self, path):
        try:
            self._set_regions_from_rows(load_puzzle(path))
            self._set_status(f"Loaded {os.path.basename(path)}. Press Solve!")
        except (OSError, ValueError) as err:
            messagebox.showerror("Couldn't load puzzle", str(err))

    def _open_file(self):
        path = filedialog.askopenfilename(
            title="Open a Star Battle puzzle", initialdir=PUZZLE_FOLDER,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:                              # empty if the user pressed Cancel
            self._load_path(path)

    def _save_file(self):
        if any(None in row for row in self.regions):
            messagebox.showwarning("Not finished", "Paint every cell before saving.")
            return
        path = filedialog.asksaveasfilename(
            title="Save puzzle", initialdir=PUZZLE_FOLDER, defaultextension=".txt",
            filetypes=[("Text files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Star Battle puzzle saved from star_battle_gui.py\n")
                for row in self.regions:
                    f.write("".join(LETTERS[k] for k in row) + "\n")
            self._set_status(f"Saved to {os.path.basename(path)}.")

    def _random_puzzle(self):
        """
        Make a random puzzle. This can take a second or two, so we do it in
        a "background thread" (a helper that works at the same time) so the
        window doesn't freeze while we wait.
        """
        self._reset_solver()
        self.random_button.configure(state="disabled")
        self._set_status("Generating a random puzzle with exactly one solution...")
        stars = self.stars_var.get()
        result = {}

        def work():                            # runs in the background thread
            try:
                result["rows"] = generate_puzzle(SIZE, stars)
            except RuntimeError as err:
                result["error"] = str(err)

        thread = threading.Thread(target=work, daemon=True)
        thread.start()

        def check():                           # runs in the window, every 100ms
            if thread.is_alive():
                self.root.after(100, check)    # not done yet, check again soon
                return
            self.random_button.configure(state="normal")
            if "error" in result:
                messagebox.showerror("Generator", result["error"])
            else:
                self._set_regions_from_rows(result["rows"])
                self._set_status("Here's a fresh random puzzle. Press Solve!")

        check()

    # ==========================================================================
    #  Running the solver
    # ==========================================================================
    def _validate(self):
        """
        Check that the painted grid makes sense before solving.
        Returns a list of rows (as letters) if OK, otherwise None.
        """
        if any(None in row for row in self.regions):
            messagebox.showwarning("Unpainted cells",
                                   "Some cells don't have a region yet. "
                                   "Paint every cell first.")
            return None
        used = {k for row in self.regions for k in row}
        if len(used) != SIZE:
            messagebox.showwarning("Wrong number of regions",
                                   f"A {SIZE}x{SIZE} puzzle needs exactly {SIZE} "
                                   f"regions, but you've used {len(used)}.")
            return None
        # Regions are normally one connected blob. Warn (but allow) if not.
        broken = [LETTERS[k] for k in sorted(used) if not self._connected(k)]
        if broken and not messagebox.askyesno(
                "Split regions",
                f"Region(s) {', '.join(broken)} are split into separate pieces. "
                "That's unusual for Star Battle. Solve anyway?"):
            return None
        return ["".join(LETTERS[k] for k in row) for row in self.regions]

    def _connected(self, k):
        """True if all cells of region k form one connected blob."""
        cells = {(r, c) for r in range(SIZE) for c in range(SIZE)
                 if self.regions[r][c] == k}
        start = next(iter(cells))
        seen, todo = {start}, [start]
        while todo:                              # "flood fill" from one cell
            r, c = todo.pop()
            for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if nb in cells and nb not in seen:
                    seen.add(nb)
                    todo.append(nb)
        return len(seen) == len(cells)

    def _start_solver(self):
        """Create a fresh solver for the current grid. Returns True if OK."""
        rows = self._validate()
        if rows is None:
            return False
        try:
            self.solver = StarBattleSolver(rows, self.stars_var.get())
        except ValueError as err:
            messagebox.showerror("Can't solve", str(err))
            return False
        self.steps = self.solver.solve_steps()   # nothing runs until asked
        self.step_count = 0
        self._clear_log()
        return True

    def _solve_or_pause(self):
        """The Solve button: start, pause or resume the animation."""
        if self.running:                       # currently playing -> pause
            self.running = False
            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self.solve_button.configure(text="Resume")
            return
        if self.steps is None and not self._start_solver():
            return
        self.running = True
        self.solve_button.configure(text="Pause")
        self._tick()

    def _tick(self):
        """Show one step, then set a timer to come back for the next one."""
        if not self.running:
            return
        if self._advance():
            self.after_id = self.root.after(self.speed.get(), self._tick)

    def _single_step(self):
        """The 'One step' button: pause and advance exactly one step."""
        if self.running:
            self._solve_or_pause()             # pause first
        if self.steps is None and not self._start_solver():
            return
        self._advance()

    def _finish_now(self):
        """The 'Skip to end' button: run all remaining steps instantly."""
        if self.steps is None and not self._start_solver():
            return
        self.running = False
        if self.after_id:                      # cancel any pending timer
            self.root.after_cancel(self.after_id)
            self.after_id = None
        # Run through the remaining steps without drawing each one
        # (drawing is the slow part), keeping only the log text.
        while self._advance(draw=False):
            pass
        self.redraw()

    def _advance(self, draw=True):
        """
        Ask the solver for its next step and display it.
        Returns False when there are no more steps (solver finished).
        """
        if self.steps is None:
            return False
        try:
            step = next(self.steps)            # <- the solver does its thing
        except StopIteration:                  # no more steps: we're done
            self._finished()
            return False
        self.step_count += 1
        self.marks = step.grid
        self.highlight = step.cells
        self.highlight_kind = step.action
        self._log(f"{self.step_count}. {step.message}", step.action)
        self._set_status(step.message)
        self._update_stats(step.depth)
        if draw:
            self.redraw()
        return True

    def _finished(self):
        """Called once the solver has nothing left to say."""
        self.running = False
        self.steps = None                      # next Solve press starts over
        self.solve_button.configure(text="Solve")
        self.highlight = []
        self.redraw()

    def _reset_solver(self):
        """Stop any solving and wipe the stars/crosses off the board."""
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.steps = None
        self.solver = None
        self.marks = None
        self.highlight = []
        self.step_count = 0
        self.solve_button.configure(text="Solve")
        self._update_stats()
        self.redraw()

    # ==========================================================================
    #  Little display helpers
    # ==========================================================================
    def _set_status(self, text):
        self.status.configure(text=text)

    def _update_stats(self, depth=0):
        guesses = self.solver.guesses if self.solver else 0
        backtracks = self.solver.backtracks if self.solver else 0
        self.stats_label.configure(
            text=f"Steps:       {self.step_count}\n"
                 f"Guesses:     {guesses}\n"
                 f"Backtracks:  {backtracks}\n"
                 f"Guess level: {depth}")

    def _log(self, text, kind):
        """Add a line to the log at the bottom, coloured by step type."""
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n", kind)
        self.log.see("end")                    # scroll to the newest line
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")


def main():
    root = tk.Tk()
    StarBattleApp(root)
    root.mainloop()                            # hand control to the window


if __name__ == "__main__":
    main()
