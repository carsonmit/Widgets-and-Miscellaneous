board = [
    [4, 0, 0, 1, 0, 2, 0, 0, 0],
    [0, 6, 0, 0, 0, 8, 3, 0, 0],
    [5, 0, 0, 0, 0, 0, 0, 0, 9],
    [0, 0, 0, 4, 0, 7, 0, 0, 8],
    [6, 8, 0, 0, 0, 5, 0, 0, 0],
    [0, 0, 4, 0, 0, 0, 0, 1, 0],
    [0, 2, 0, 0, 0, 0, 5, 0, 0],
    [0, 0, 0, 0, 7, 0, 2, 0, 6],
    [0, 9, 0, 0, 0, 6, 7, 0, 0]
]


# Prints a properly formatted sudoku board
def printBoard(board):
    for i in range(9):
        if i % 3 == 0 and i != 0:
            print("- - - - - - - - - - - -")  # Prints a horizontal bar after every 3rd row
        for j in range(9):
            if j % 3 == 0 and j != 0:
                print(" | ", end="")  # Prints a vertical bar after every 3rd entry in each row
            if j == 8:
                print(board[i][j])  # Prints last entry in each row w a new line and w/o an extra space
            else:
                print(str(board[i][j]), end=" ")  # Prints all other entries w a space in between and no new line


# Locates the first empty cell on the board and returns its coords, returns none if board is full
def findEmpty(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return i, j  # Coords of empty cell
    return None


# Takes a number n and a cell (i, j) and returns true if n is a valid entry for the cell
def isValid(board, n, cell):
    # First, row i is checked for other entries equal to n. If found, placement is invalid
    for i in range(9):
        if board[cell[0]][i] == n and cell[1] != i:
            return False
    # Second, column j is checked for other entries equal to n. If found, placement is invalid
    for i in range(9):
        if board[i][cell[1]] == n and cell[0] != i:
            return False
    # Finally, the square containing the cell is checked for the same criteria
    x = cell[1] // 3  # Assigns 0, 1, 2 - the x-coordinate of the box
    y = cell[0] // 3  # The y-coordinate of the box, top left is (0,0) bottom right is (2,2)
    for i in range(y*3, y*3 + 3):  # Iterates through the 3 rows of the box
        for j in range(x*3, x*3 + 3):  # Iterates through the each of the 3 entries for each row
            if board[i][j] == n and (i, j) != cell:
                return False
    return True  # Valid if all three tests pass


def solve(board):
    emptyCell = findEmpty(board)  # Finds the first empty cell using findEmpty
    if not emptyCell:
        return True  # Board is solved if all cells are filled
    else:
        row, col = emptyCell  # Assigns empty cell coords to row and col if it exists
    for i in range(9):
        if isValid(board, i + 1, (row, col)):
            board[row][col] = i + 1  # Finds first valid number for cell using isValid and assigns it
            if solve(board):
                return True  # Recursively runs solve on new board and continues until solution is found
            board[row][col] = 0  # If the next iteration of solve returns false for all values 1-9, previous entry is
                # reset to 0 and next possible entry is tried instead (backtracking)
    return False

printBoard(board)
solve(board)
print("~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~")
print("")
print("~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~")
printBoard(board)


# Graphical user interface
import pygame
import time
pygame.font.init()

class Grid:
    board = [
        [4, 0, 0, 1, 0, 2, 0, 0, 0],
        [0, 6, 0, 0, 0, 8, 3, 0, 0],
        [5, 0, 0, 0, 0, 0, 0, 0, 9],
        [0, 0, 0, 4, 0, 7, 0, 0, 8],
        [6, 8, 0, 0, 0, 5, 0, 0, 0],
        [0, 0, 4, 0, 0, 0, 0, 1, 0],
        [0, 2, 0, 0, 0, 0, 5, 0, 0],
        [0, 0, 0, 0, 7, 0, 2, 0, 6],
        [0, 9, 0, 0, 0, 6, 7, 0, 0]
    ]

    def __init__(self, rows, cols, width, height, win):
        self.rows = rows
        self.cols = cols
        self.cubes = [[Cube(self.board[i][j], i, j, width, height) for j in range(cols)] for i in range(rows)]
        self.width = width
        self.height = height
        self.model = None
        self.update_model()
        self.selected = None
        self.win = win

    def update_model(self):
        self.model = [[self.cubes[i][j].value for j in range(self.cols)] for i in range(self.rows)]

    def place(self, val):
        row, col = self.selected
        if self.cubes[row][col].value == 0:
            self.cubes[row][col].set(val)
            self.update_model()
            if valid(self.model, val, (row,col)) and self.solve():
                return True
            else:
                self.cubes[row][col].set(0)
                self.cubes[row][col].set_temp(0)
                self.update_model()
                return False

    def sketch(self, val):
        row, col = self.selected
        self.cubes[row][col].set_temp(val)

    def draw(self):
        # Draw Grid Lines
        gap = self.width / 9
        for i in range(self.rows+1):
            if i % 3 == 0 and i != 0:
                thick = 4
            else:
                thick = 1
            pygame.draw.line(self.win, (0,0,0), (0, i*gap), (self.width, i*gap), thick)
            pygame.draw.line(self.win, (0, 0, 0), (i * gap, 0), (i * gap, self.height), thick)
        # Draw Cubes
        for i in range(self.rows):
            for j in range(self.cols):
                self.cubes[i][j].draw(self.win)

    def select(self, row, col):
        # Reset all other
        for i in range(self.rows):
            for j in range(self.cols):
                self.cubes[i][j].selected = False
        self.cubes[row][col].selected = True
        self.selected = (row, col)

    def clear(self):
        row, col = self.selected
        if self.cubes[row][col].value == 0:
            self.cubes[row][col].set_temp(0)

    def click(self, pos):
        """ :param: pos
        :return: (row, col) """
        if pos[0] < self.width and pos[1] < self.height:
            gap = self.width / 9
            x = pos[0] // gap
            y = pos[1] // gap
            return (int(y),int(x))
        else:
            return None

    def is_finished(self):
        for i in range(self.rows):
            for j in range(self.cols):
                if self.cubes[i][j].value == 0:
                    return False
        return True

    def solve_gui(self):
        self.update_model()
        find = findEmpty(self.model)
        if not find:
            return True
        else:
            row, col = find
        for i in range(1, 10):
            if isValid(self.model, i, (row, col)):
                self.model[row][col] = i
                self.cubes[row][col].set(i)
                self.cubes[row][col].draw_change(self.win, True)
                self.update_model()
                pygame.display.update()
                pygame.time.delay(100)
                if self.solve_gui():
                    return True
                self.model[row][col] = 0
                self.cubes[row][col].set(0)
                self.update_model()
                self.cubes[row][col].draw_change(self.win, False)
                pygame.display.update()
                pygame.time.delay(100)
        return False

class Cube:
    rows = 9
    cols = 9

    def __init__(self, value, row, col, width, height):
        self.value = value
        self.temp = 0
        self.row = row
        self.col = col
        self.width = width
        self.height = height
        self.selected = False

    def draw(self, win):
        fnt = pygame.font.SysFont("comicsans", 40)
        gap = self.width / 9
        x = self.col * gap
        y = self.row * gap
        if self.temp != 0 and self.value == 0:
            text = fnt.render(str(self.temp), 1, (128,128,128))
            win.blit(text, (x+5, y+5))
        elif not(self.value == 0):
            text = fnt.render(str(self.value), 1, (0, 0, 0))
            win.blit(text, (x + (gap/2 - text.get_width()/2), y + (gap/2 - text.get_height()/2)))
        if self.selected:
            pygame.draw.rect(win, (255,0,0), (x,y, gap ,gap), 3)

    def draw_change(self, win, g=True):
        fnt = pygame.font.SysFont("comicsans", 40)
        gap = self.width / 9
        x = self.col * gap
        y = self.row * gap
        pygame.draw.rect(win, (255, 255, 255), (x, y, gap, gap), 0)
        text = fnt.render(str(self.value), 1, (0, 0, 0))
        win.blit(text, (x + (gap / 2 - text.get_width() / 2), y + (gap / 2 - text.get_height() / 2)))
        if g:
            pygame.draw.rect(win, (0, 255, 0), (x, y, gap, gap), 3)
        else:
            pygame.draw.rect(win, (255, 0, 0), (x, y, gap, gap), 3)

    def set(self, val):
        self.value = val

    def set_temp(self, val):
        self.temp = val

def redraw_window(win, board, time, strikes):
    win.fill((255,255,255))
    # Draw time
    fnt = pygame.font.SysFont("comicsans", 40)
    text = fnt.render("Time: " + format_time(time), 1, (0,0,0))
    win.blit(text, (540 - 160, 560))
    # Draw Strikes
    text = fnt.render("X " * strikes, 1, (255, 0, 0))
    win.blit(text, (20, 560))
    # Draw grid and board
    board.draw()

def format_time(secs):
    sec = secs%60
    minute = secs//60
    hour = minute//60
    mat = " " + str(minute) + ":" + str(sec)
    return mat

def main():
    win = pygame.display.set_mode((540,600))
    pygame.display.set_caption("Sudoku")
    board = Grid(9, 9, 540, 540, win)
    key = None
    run = True
    start = time.time()
    strikes = 0
    while run:
        play_time = round(time.time() - start)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    key = 1
                if event.key == pygame.K_2:
                    key = 2
                if event.key == pygame.K_3:
                    key = 3
                if event.key == pygame.K_4:
                    key = 4
                if event.key == pygame.K_5:
                    key = 5
                if event.key == pygame.K_6:
                    key = 6
                if event.key == pygame.K_7:
                    key = 7
                if event.key == pygame.K_8:
                    key = 8
                if event.key == pygame.K_9:
                    key = 9
                if event.key == pygame.K_KP1:
                    key = 1
                if event.key == pygame.K_KP2:
                    key = 2
                if event.key == pygame.K_KP3:
                    key = 3
                if event.key == pygame.K_KP4:
                    key = 4
                if event.key == pygame.K_KP5:
                    key = 5
                if event.key == pygame.K_KP6:
                    key = 6
                if event.key == pygame.K_KP7:
                    key = 7
                if event.key == pygame.K_KP8:
                    key = 8
                if event.key == pygame.K_KP9:
                    key = 9
                if event.key == pygame.K_DELETE:
                    board.clear()
                    key = None
                if event.key == pygame.K_SPACE:
                    board.solve_gui()
                if event.key == pygame.K_RETURN:
                    i, j = board.selected
                    if board.cubes[i][j].temp != 0:
                        if board.place(board.cubes[i][j].temp):
                            print("Success")
                        else:
                            print("Wrong")
                            strikes += 1
                        key = None
                        if board.is_finished():
                            print("Game over")
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                clicked = board.click(pos)
                if clicked:
                    board.select(clicked[0], clicked[1])
                    key = None
        if board.selected and key != None:
            board.sketch(key)
        redraw_window(win, board, play_time, strikes)
        pygame.display.update()

main()
pygame.quit()