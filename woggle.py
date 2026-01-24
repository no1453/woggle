# ═══════════════════════════════════════════════════════════════════════════
# Woggle 1.3.0 - An Oddly Familiar Word Game
# by no1453@gmail.com
# 2026.01.23
# A Boggle-style word game with timer, scoring, and cheat mode
# REFACTORED: Game state now managed by GameState class
# ═══════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────
# IMPORTS
# Required libraries for game functionality, graphics, and sound
# ───────────────────────────────────────────────────────────────────────────
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")

import pygame
import random
import time
import numpy as np

# ───────────────────────────────────────────────────────────────────────────
# BOGGLE DICE CONFIGURATION
# Standard Boggle dice with their six faces each. Each die is represented as
# a list of strings, where each string is a possible letter or digraph like "Qu".
# ───────────────────────────────────────────────────────────────────────────
CUBES = [
    ["A", "A", "C", "I", "O", "T"],
    ["A", "B", "I", "L", "T", "Y"],
    ["A", "B", "J", "M", "O", "Qu"],
    ["A", "C", "D", "E", "M", "P"],
    ["A", "C", "E", "L", "R", "S"],
    ["A", "D", "E", "N", "V", "Z"],
    ["A", "H", "M", "O", "R", "S"],
    ["B", "I", "F", "O", "R", "X"],
    ["D", "E", "N", "O", "S", "W"],
    ["D", "K", "N", "O", "T", "U"],
    ["E", "E", "F", "H", "I", "Y"],
    ["E", "G", "I", "N", "T", "V"],
    ["E", "G", "K", "L", "U", "Y"],
    ["E", "H", "I", "N", "P", "S"],
    ["E", "L", "P", "S", "T", "U"],
    ["G", "I", "L", "R", "U", "W"]
]

# ═══════════════════════════════════════════════════════════════════════════
# GAME CONSTANTS
# Define dimensions, colors, and other constants used throughout the game.
# ═══════════════════════════════════════════════════════════════════════════

# Grid dimensions for the 4x4 board
GRID_SIZE = 4
CELL_SIZE = 100
GRID_WIDTH = GRID_SIZE * CELL_SIZE + 40  # Add 40 pixels for 20px border on each side

# Panel dimensions for sidebars and UI elements
SIDE_PANEL = 250
BASE_WIDTH = GRID_WIDTH + SIDE_PANEL
CHEAT_PANEL_WIDTH = 300
SCREEN_HEIGHT = GRID_SIZE * CELL_SIZE + 40 + 180  # Add 40 pixels for border

# Timer configuration
TIME_LIMIT = 180  # 3 minutes in seconds

# Scrolling configuration
WORD_LINE_HEIGHT = 28
WORDS_AREA_Y = 70
WORDS_AREA_HEIGHT = 352
WORDS_AREA_WIDTH = SIDE_PANEL - 40

# Color palette used for UI elements
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (230, 230, 230)
BLUE = (100, 150, 255)
DARK_BLUE = (70, 120, 220)
NAVY_BLUE = (20, 60, 140)
YELLOW = (255, 255, 100)
RED = (220, 50, 50)
GREEN = (0, 180, 0)
SCROLLBAR_COLOR = (120, 120, 120)
SCROLLBAR_ACTIVE = (90, 90, 90)

# ───────────────────────────────────────────────────────────────────────────
# PYGAME AND AUDIO INITIALIZATION
# Initialize Pygame for graphics and mixer for sound effects. The mixer is
# configured with a sample rate of 48000 Hz, 16-bit signed audio, and a buffer
# size of 512. The number of channels is detected from the system.
# ───────────────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=512)
num_channels = pygame.mixer.get_init()[2]  # Detect actual number of audio channels

# ───────────────────────────────────────────────────────────────────────────
# SOUND GENERATION FUNCTIONS
# Create procedural sound effects using numpy sine waves for positive and
# negative feedback. These functions generate short audio clips dynamically.
# ───────────────────────────────────────────────────────────────────────────

def make_ding():
    """
    Generate a pleasant 'ding' sound for positive feedback.
    Uses a 1500 Hz sine wave with exponential decay for a clean, bell-like tone.
    """
    sample_rate = 48000
    duration = 0.075
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.25 * np.sin(2 * np.pi * 1500 * t) * np.exp(-t * 16)

    # Create mono or multi-channel audio based on system configuration
    if num_channels == 1:
        sound_array = (wave * 32767).astype(np.int16)
    else:
        stereo_wave = np.column_stack([wave] * num_channels)
        sound_array = (stereo_wave * 32767).astype(np.int16)

    sound_array = np.ascontiguousarray(sound_array)
    return pygame.sndarray.make_sound(sound_array)

def make_buzzer():
    """
    Generate a 'buzzer' sound for negative feedback.
    Uses a 150 Hz square wave with exponential decay for a harsh, alerting tone.
    """
    sample_rate = 48000
    duration = 0.075
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.2 * np.sign(np.sin(2 * np.pi * 150 * t)) * np.exp(-t * 5)

    # Create mono or multi-channel audio based on system configuration
    if num_channels == 1:
        sound_array = (wave * 32767).astype(np.int16)
    else:
        stereo_wave = np.column_stack([wave] * num_channels)
        sound_array = (stereo_wave * 32767).astype(np.int16)

    sound_array = np.ascontiguousarray(sound_array)
    return pygame.sndarray.make_sound(sound_array)

# Create sound effect instances for immediate use in the game
ding_sound = make_ding()
buzzer_sound = make_buzzer()

# ───────────────────────────────────────────────────────────────────────────
# DICTIONARY LOADING
# Load valid words from an external file named "words" and build a prefix set
# for fast lookup and pruning during word searches. Only words of 3 or more
# letters are included.
# ───────────────────────────────────────────────────────────────────────────
dictionary = set()
dictionary_load_error = None

try:
    with open("words", "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().upper()
            if word and 3 <= len(word) <= 16:  # Only accept words 3-16 letters
                dictionary.add(word)

    # Validate dictionary was loaded successfully
    if len(dictionary) == 0:
        dictionary_load_error = "Warning: 'words' file is empty or contains no valid words."
        print(dictionary_load_error)

except FileNotFoundError:
    dictionary_load_error = "Warning: 'words' file not found. Game will run but no words will be valid."
    print(dictionary_load_error)

except UnicodeDecodeError as e:
    dictionary_load_error = f"Warning: 'words' file has encoding issues: {e}. Trying alternate encoding..."
    print(dictionary_load_error)
    # Try with latin-1 encoding as fallback (handles most Western text)
    try:
        with open("words", "r", encoding="latin-1") as f:
            for line in f:
                word = line.strip().upper()
                if word and 3 <= len(word) <= 16:
                    dictionary.add(word)
        if len(dictionary) > 0:
            print(f"Successfully loaded {len(dictionary)} words with fallback encoding.")
            dictionary_load_error = None
    except Exception as e2:
        dictionary_load_error = f"Error: Could not load dictionary with fallback encoding: {e2}"
        print(dictionary_load_error)

except PermissionError:
    dictionary_load_error = "Error: Permission denied when trying to read 'words' file."
    print(dictionary_load_error)

except Exception as e:
    dictionary_load_error = f"Error loading dictionary: {e}"
    print(dictionary_load_error)

# Build prefix set for efficient word search pruning
# This dramatically speeds up the DFS search by eliminating impossible paths early
prefixes = set()
for word in dictionary:
    for i in range(1, len(word) + 1):
        prefixes.add(word[:i])

# ───────────────────────────────────────────────────────────────────────────
# DRAWING HELPER FUNCTIONS
# Utility functions for drawing custom shapes.
# ───────────────────────────────────────────────────────────────────────────

def draw_rounded_rect(surface, color, rect, border_radius=10, border_width=0, border_color=None):
    """
    Draw a rectangle with rounded corners.

    Args:
        surface: Pygame surface to draw on
        color: Fill color for the rectangle
        rect: pygame.Rect or (x, y, width, height) tuple
        border_radius: Radius of the rounded corners
        border_width: Width of the border (0 for no border)
        border_color: Color of the border (if border_width > 0)
    """
    if isinstance(rect, tuple):
        rect = pygame.Rect(rect)

    # Draw filled rounded rectangle
    pygame.draw.rect(surface, color, rect, border_radius=border_radius)

    # Draw border if requested
    if border_width > 0 and border_color:
        pygame.draw.rect(surface, border_color, rect, width=border_width, border_radius=border_radius)


# ═══════════════════════════════════════════════════════════════════════════
# GAME STATE CLASS
# Encapsulates all game state and logic in a single class for better
# organization, testability, and maintainability.
# ═══════════════════════════════════════════════════════════════════════════

class GameState:
    """
    Manages all game state including board, score, timer, and UI state.

    This class encapsulates the entire game state, making it easier to:
    - Reset the game (just create a new instance or call reset())
    - Test game logic in isolation
    - Save/load game state
    - Track multiple games
    """

    def __init__(self):
        """Initialize a new game with a fresh board and reset state."""
        self.reset()

    def reset(self):
        """Reset all game state to start a new game."""
        # Board and word tracking
        self.board = self._generate_board()
        self.selected_path = []           # Current word being built by user
        self.found_words = []             # List of (word, tile_count) tuples
        self.score = 0                    # Current score

        # Timer state
        self.timer_active = False         # Is timer currently running?
        self.timer_start = 0              # Time when timer was started
        self.total_elapsed = 0            # Total elapsed time (for pause/resume)

        # Found words panel scrolling
        self.scroll_offset = 0
        self.dragging_scrollbar = False

        # Countdown sound tracking (to play once per second)
        self.last_countdown_second = -1

        # Cheat mode state
        self.cheat_visible = False              # Is cheat panel currently shown?
        self.cheat_scroll_offset = 0            # Scroll position in cheat list
        self.cheat_dragging_scrollbar = False   # Is user dragging cheat scrollbar?
        self.selected_cheat_word = None         # Currently selected word in cheat list
        self.selected_path_from_cheat = []      # Path to show for selected cheat word

        # Possible words cache
        self.possible_words = self._find_all_possible_words()

    def _generate_board(self):
        """
        Generate a random 4x4 Boggle board.
        Shuffles the dice, then picks one random face from each die.
        Returns a flat list of 16 letters.
        """
        shuffled = CUBES[:]
        random.shuffle(shuffled)
        return [random.choice(cube) for cube in shuffled]

    def reshuffle(self):
        """Generate a new board and reset game state, preserving cheat panel visibility."""
        was_cheat_visible = self.cheat_visible
        self.reset()
        self.cheat_visible = was_cheat_visible

    # ───────────────────────────────────────────────────────────────────────
    # ADJACENCY AND VALIDATION
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def is_adjacent(pos1, pos2):
        """
        Check if two board positions are adjacent (including diagonals).

        Args:
            pos1, pos2: Tuples of (row, col) coordinates

        Returns:
            True if positions are adjacent, False otherwise
        """
        r1, c1 = pos1
        r2, c2 = pos2
        return max(abs(r1 - r2), abs(c1 - c2)) == 1 and pos1 != pos2

    def is_valid_word(self, word, path):
        """
        Validate that a word is legal according to Boggle rules.

        Checks:
        - Word is at least 3 letters
        - Word exists in dictionary
        - Path length matches word length (accounting for "QU")
        - All positions in path are adjacent

        Args:
            word: The word string to validate
            path: List of (row, col) positions forming the word

        Returns:
            True if word is valid, False otherwise
        """
        if len(word) < 3 or word not in dictionary:
            return False

        # Count how many "Qu" tiles are in the path
        qu_count = sum(1 for r, c in path if self.board[r * GRID_SIZE + c] == "Qu")

        # Expected word length = path length + number of "Qu" tiles
        expected_word_length = len(path) + qu_count

        if len(word) != expected_word_length:
            return False

        # Verify all positions are adjacent
        for i in range(1, len(path)):
            if not self.is_adjacent(path[i-1], path[i]):
                return False

        return True

    # ───────────────────────────────────────────────────────────────────────
    # SCORING
    # ───────────────────────────────────────────────────────────────────────

    @staticmethod
    def calculate_score(tile_count):
        """
        Calculate score for a word based on tile count.

        Args:
            tile_count: Number of tiles used (path length)

        Returns:
            Point value for the word
        """
        if tile_count <= 4:
            return 1
        elif tile_count == 5:
            return 2
        elif tile_count == 6:
            return 3
        elif tile_count == 7:
            return 5
        else:
            return 11

    def submit_word(self):
        """
        Attempt to submit the currently selected word.

        Returns:
            True if word was valid and added, False otherwise
        """
        if not self.selected_path:
            return False

        # Build word string from selected path
        word = "".join(
            self.board[r * GRID_SIZE + c].replace("Qu", "QU")
            for r, c in self.selected_path
        ).upper()

        # Check if word already found
        found_word_strings = [w for w, tc in self.found_words]

        if self.is_valid_word(word, self.selected_path) and word not in found_word_strings:
            # Valid new word! Store word with its tile count
            tile_count = len(self.selected_path)
            self.found_words.append((word, tile_count))

            # Calculate and add score
            self.score += self.calculate_score(tile_count)

            # Auto-scroll to show new word at bottom
            self.scroll_offset = -max(0, len(self.found_words) * WORD_LINE_HEIGHT - WORDS_AREA_HEIGHT)

            self.selected_path = []
            return True

        self.selected_path = []
        return False

    def get_current_word(self):
        """Get the word currently being built from selected path."""
        return "".join(
            self.board[r * GRID_SIZE + c].replace("Qu", "QU")
            for r, c in self.selected_path
        ).upper()

    # ───────────────────────────────────────────────────────────────────────
    # TIMER MANAGEMENT
    # ───────────────────────────────────────────────────────────────────────

    def toggle_timer(self):
        """Toggle timer on/off, tracking elapsed time for pauses."""
        if self.timer_active:
            # Pause timer - save elapsed time
            self.total_elapsed += time.time() - self.timer_start
            self.timer_active = False
        else:
            # Start/resume timer
            self.timer_start = time.time()
            self.timer_active = True

    def reset_timer(self):
        """Reset timer to initial state."""
        self.timer_active = False
        self.total_elapsed = 0
        self.timer_start = 0
        self.selected_path = []

    def get_time_left(self):
        """
        Calculate remaining time.

        Returns:
            Seconds remaining (0 if timer expired)
        """
        if self.timer_active:
            current_elapsed = time.time() - self.timer_start + self.total_elapsed
            time_left = max(0, TIME_LIMIT - int(current_elapsed))
            if time_left <= 0:
                self.timer_active = False
            return time_left
        else:
            return max(0, TIME_LIMIT - int(self.total_elapsed))

    # ───────────────────────────────────────────────────────────────────────
    # WORD SELECTION
    # ───────────────────────────────────────────────────────────────────────

    def select_letter(self, row, col):
        """
        Handle selection of a letter on the board.

        Args:
            row, col: Grid coordinates of selected letter

        Returns:
            True if selection was valid, False otherwise
        """
        pos = (row, col)

        if not self.selected_path:
            # Start new word
            self.selected_path = [pos]
            return True
        elif pos == self.selected_path[0]:
            # Clicked first letter again - clear selection
            self.selected_path = []
            return True
        elif pos not in self.selected_path and self.is_adjacent(self.selected_path[-1], pos):
            # Add adjacent letter to word
            self.selected_path.append(pos)
            return True

        return False

    # ───────────────────────────────────────────────────────────────────────
    # CHEAT MODE
    # ───────────────────────────────────────────────────────────────────────

    def toggle_cheat(self):
        """Toggle cheat panel visibility."""
        self.cheat_visible = not self.cheat_visible
        if not self.cheat_visible:
            self.selected_cheat_word = None
            self.selected_path_from_cheat = []

    def select_cheat_word(self, word):
        """
        Select a word from the cheat list to highlight on board.

        Args:
            word: The word to select (or None to deselect)
        """
        if word == self.selected_cheat_word:
            # Toggle off
            self.selected_cheat_word = None
            self.selected_path_from_cheat = []
        else:
            path = self.find_path_for_word(word)
            if path:
                self.selected_cheat_word = word
                self.selected_path_from_cheat = path

    # ───────────────────────────────────────────────────────────────────────
    # WORD FINDING ALGORITHMS
    # ───────────────────────────────────────────────────────────────────────

    def _find_all_possible_words(self):
        """
        Find all valid words that can be formed on the current board.
        Uses depth-first search with prefix pruning for efficiency.

        Returns:
            Sorted list of all possible words
        """
        board = self.board

        def get_letter(idx):
            """Get letter at index, converting 'Qu' to 'QU'"""
            return "QU" if board[idx] == "Qu" else board[idx]

        def dfs(pos, visited, current_word):
            """Depth-first search to find words starting from position."""
            if len(current_word) > 16:
                return

            letter = get_letter(pos)
            current_word += letter

            # Prune: if no dictionary word starts with this prefix, stop
            if current_word not in prefixes:
                return

            # If we found a valid word, add it to results
            if len(current_word) >= 3 and current_word in dictionary:
                found.add(current_word)

            # Explore all adjacent positions
            r, c = divmod(pos, GRID_SIZE)
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == dc == 0:
                        continue

                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 4 and 0 <= nc < 4:
                        new_pos = nr * 4 + nc
                        if new_pos not in visited:
                            visited.add(new_pos)
                            dfs(new_pos, visited, current_word)
                            visited.remove(new_pos)

        # Try starting from each position on the board
        found = set()
        for start_pos in range(16):
            visited = {start_pos}
            dfs(start_pos, visited, "")

        return sorted(found)

    def find_path_for_word(self, target):
        """
        Find a valid path on the board that spells the target word.
        Used for the cheat mode to show where words can be found.

        Args:
            target: The word to find

        Returns:
            List of (row, col) positions forming the word, or None if not found
        """
        target = target.upper()
        board = self.board

        def get_letter(idx):
            """Get letter at index, converting 'Qu' to 'QU'"""
            return "QU" if board[idx] == "Qu" else board[idx]

        def dfs(pos, path, current):
            """Depth-first search to find path for target word."""
            if current == target:
                return path[:]

            if len(current) >= len(target):
                return None

            r, c = divmod(pos, GRID_SIZE)
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == dc == 0:
                        continue

                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 4 and 0 <= nc < 4:
                        np_idx = nr * 4 + nc

                        if np_idx not in {p[0] * 4 + p[1] for p in path}:
                            next_l = get_letter(np_idx)
                            new = current + next_l

                            if target.startswith(new):
                                path.append((nr, nc))
                                res = dfs(np_idx, path, new)
                                if res:
                                    return res
                                path.pop()

            return None

        # Try starting from each position
        for start in range(16):
            start_l = get_letter(start)
            if target.startswith(start_l):
                sr, sc = divmod(start, 4)
                res = dfs(start, [(sr, sc)], start_l)
                if res:
                    return res

        return None

    # ───────────────────────────────────────────────────────────────────────
    # SERIALIZATION (for future save/load feature)
    # ───────────────────────────────────────────────────────────────────────

    def to_dict(self):
        """
        Convert game state to a dictionary for serialization.

        Returns:
            Dictionary containing all game state
        """
        return {
            'board': self.board,
            'found_words': self.found_words,
            'score': self.score,
            'total_elapsed': self.total_elapsed + (
                time.time() - self.timer_start if self.timer_active else 0
            ),
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a GameState from a dictionary.

        Args:
            data: Dictionary containing game state

        Returns:
            New GameState instance
        """
        game = cls()
        game.board = data['board']
        game.found_words = data['found_words']
        game.score = data['score']
        game.total_elapsed = data['total_elapsed']
        game.possible_words = game._find_all_possible_words()
        return game


# ───────────────────────────────────────────────────────────────────────────
# BUTTON DEFINITIONS
# Pre-defined rectangles for all interactive buttons in the UI.
# ───────────────────────────────────────────────────────────────────────────
submit_rect       = pygame.Rect(0, GRID_SIZE * CELL_SIZE + 40, GRID_WIDTH, 60)
timer_toggle_rect = pygame.Rect(0, GRID_SIZE * CELL_SIZE + 100, GRID_WIDTH // 2, 60)
timer_reset_rect  = pygame.Rect(GRID_WIDTH // 2, GRID_SIZE * CELL_SIZE + 100, GRID_WIDTH // 2, 60)
reshuffle_rect    = pygame.Rect(0, GRID_SIZE * CELL_SIZE + 160, GRID_WIDTH // 2, 60)
cheat_rect        = pygame.Rect(GRID_WIDTH // 2, GRID_SIZE * CELL_SIZE + 160, GRID_WIDTH // 2, 60)

# Fonts for different text sizes in the UI
font = pygame.font.SysFont(None, 60)          # Large font for board letters
small_font = pygame.font.SysFont(None, 32)    # Small font for UI text
button_font = pygame.font.SysFont(None, 36)   # Medium font for buttons

# ───────────────────────────────────────────────────────────────────────────
# SPLASH SCREEN - borderless
# ───────────────────────────────────────────────────────────────────────────

try:
    splash_img = pygame.image.load("woggleSplash.png")
    splash_img = pygame.transform.scale(splash_img, (BASE_WIDTH, SCREEN_HEIGHT))

    # Create borderless window for splash
    splash_screen = pygame.display.set_mode((BASE_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("Woggle")

    splash_screen.blit(splash_img, (0, 0))
    pygame.display.flip()

    # Show for ~3 seconds, allow early exit
    splash_start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - splash_start < 3000:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                break
        else:
            continue
        break

except Exception as e:
    print(f"Splash screen failed: {e}")

# ───────────────────────────────────────────────────────────────────────────
# WINDOW INITIALIZATION
# Set up the main game window with initial size and caption.
# ───────────────────────────────────────────────────────────────────────────
screen = pygame.display.set_mode((BASE_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Woggle - An Oddly Familiar Word Game")

# Set custom window icon (optional - file must exist)
try:
    icon = pygame.image.load("woggle.ico")
    pygame.display.set_icon(icon)
except:
    pass  # If icon file not found, just use default

# ───────────────────────────────────────────────────────────────────────────
# CREATE GAME INSTANCE
# ───────────────────────────────────────────────────────────────────────────
game = GameState()

# Scrollbar UI constants
scrollbar_width = 10
scrollbar_x = BASE_WIDTH - scrollbar_width - 15  # Position inside the word list box

# ═══════════════════════════════════════════════════════════════════════════
# MAIN GAME LOOP
# Handles events, updates game state, and renders the screen at 60 FPS.
# ═══════════════════════════════════════════════════════════════════════════

running = True
clock = pygame.time.Clock()

while running:
    # ───────────────────────────────────────────────────────────────────────
    # EVENT HANDLING
    # Process all Pygame events, including mouse clicks, drags, and wheel scrolls.
    # ───────────────────────────────────────────────────────────────────────

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # Only process left mouse button
            if event.button != 1:
                continue

            # ───────────────────────────────────────────────────────────────
            # BOARD LETTER SELECTION
            # ───────────────────────────────────────────────────────────────
            if mx < GRID_WIDTH and my < GRID_SIZE * CELL_SIZE + 40:
                adjusted_mx = mx - 20
                adjusted_my = my - 20

                if 0 <= adjusted_mx < GRID_SIZE * CELL_SIZE and 0 <= adjusted_my < GRID_SIZE * CELL_SIZE:
                    col = adjusted_mx // CELL_SIZE
                    row = adjusted_my // CELL_SIZE

                    if not game.select_letter(row, col):
                        buzzer_sound.play()

            # ───────────────────────────────────────────────────────────────
            # SUBMIT WORD BUTTON
            # ───────────────────────────────────────────────────────────────
            if submit_rect.collidepoint(mx, my) and game.selected_path:
                if game.submit_word():
                    ding_sound.play()
                else:
                    buzzer_sound.play()

            # ───────────────────────────────────────────────────────────────
            # TIMER START/STOP BUTTON
            # ───────────────────────────────────────────────────────────────
            if timer_toggle_rect.collidepoint(mx, my):
                game.toggle_timer()
                ding_sound.play()

            # ───────────────────────────────────────────────────────────────
            # RESET TIMER BUTTON
            # ───────────────────────────────────────────────────────────────
            if timer_reset_rect.collidepoint(mx, my):
                game.reset_timer()
                ding_sound.play()

            # ───────────────────────────────────────────────────────────────
            # RE-SHUFFLE BUTTON
            # ───────────────────────────────────────────────────────────────
            if reshuffle_rect.collidepoint(mx, my):
                game.reshuffle()
                ding_sound.play()

            # ───────────────────────────────────────────────────────────────
            # CHEAT BUTTON
            # ───────────────────────────────────────────────────────────────
            if cheat_rect.collidepoint(mx, my):
                game.toggle_cheat()

                if game.cheat_visible:
                    screen = pygame.display.set_mode((BASE_WIDTH + CHEAT_PANEL_WIDTH, SCREEN_HEIGHT))
                    pygame.display.set_caption("Woggle – An Oddly Familiar Word Game - Cheat Mode")
                else:
                    screen = pygame.display.set_mode((BASE_WIDTH, SCREEN_HEIGHT))
                    pygame.display.set_caption("Woggle - An Oddly Familiar Word Game")

                ding_sound.play()

            # ───────────────────────────────────────────────────────────────
            # MAIN PANEL SCROLLBAR
            # ───────────────────────────────────────────────────────────────
            if len(game.found_words) * WORD_LINE_HEIGHT > WORDS_AREA_HEIGHT:
                content_h = len(game.found_words) * WORD_LINE_HEIGHT
                max_scroll = content_h - WORDS_AREA_HEIGHT
                if content_h > 0 and max_scroll > 0:
                    thumb_h = max(30, (WORDS_AREA_HEIGHT / content_h) * WORDS_AREA_HEIGHT)
                    thumb_y = WORDS_AREA_Y + (-game.scroll_offset / max_scroll) * (WORDS_AREA_HEIGHT - thumb_h)
                    sb_rect = pygame.Rect(scrollbar_x, thumb_y, scrollbar_width, thumb_h)
                    if sb_rect.collidepoint(mx, my):
                        game.dragging_scrollbar = True

            # ───────────────────────────────────────────────────────────────
            # CHEAT PANEL SCROLLBAR
            # ───────────────────────────────────────────────────────────────
            if game.cheat_visible:
                cheat_top = 65
                cheat_h = SCREEN_HEIGHT - 95
                content_h = len(game.possible_words) * 24
                max_scroll = content_h - cheat_h
                if content_h > cheat_h and max_scroll > 0:
                    thumb_h = max(30, (cheat_h / content_h) * cheat_h)
                    thumb_y = cheat_top + (-game.cheat_scroll_offset / max_scroll) * (cheat_h - thumb_h)
                    sb_rect = pygame.Rect(BASE_WIDTH + CHEAT_PANEL_WIDTH - 20, thumb_y, 14, thumb_h)
                    if sb_rect.collidepoint(mx, my):
                        game.cheat_dragging_scrollbar = True
                        continue

            # ───────────────────────────────────────────────────────────────
            # CHEAT WORD SELECTION
            # ───────────────────────────────────────────────────────────────
            if game.cheat_visible and mx >= BASE_WIDTH and not game.cheat_dragging_scrollbar:
                cheat_top = 65
                line_h = 24
                cheat_h = SCREEN_HEIGHT - 95

                cheat_area = pygame.Rect(BASE_WIDTH + 5, cheat_top, CHEAT_PANEL_WIDTH - 30, cheat_h)
                if cheat_area.collidepoint(mx, my):
                    for i, word in enumerate(game.possible_words):
                        y = cheat_top + i * line_h + game.cheat_scroll_offset
                        if cheat_top <= y <= cheat_top + cheat_h - line_h:
                            if y <= my <= y + line_h:
                                game.select_cheat_word(word)
                                ding_sound.play()
                                break

        # ───────────────────────────────────────────────────────────────────
        # MOUSE BUTTON RELEASE
        # ───────────────────────────────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONUP:
            game.dragging_scrollbar = False
            game.cheat_dragging_scrollbar = False

        # ───────────────────────────────────────────────────────────────────
        # MOUSE MOTION (DRAGGING)
        # ───────────────────────────────────────────────────────────────────
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos

            if game.dragging_scrollbar:
                content_h = len(game.found_words) * WORD_LINE_HEIGHT
                if content_h > 0:
                    thumb_h = max(30, (WORDS_AREA_HEIGHT / content_h) * WORDS_AREA_HEIGHT)
                    max_off = content_h - WORDS_AREA_HEIGHT
                    rel_y = my - WORDS_AREA_Y - thumb_h / 2
                    if WORDS_AREA_HEIGHT - thumb_h > 0:
                        ratio = max(0, min(1, rel_y / (WORDS_AREA_HEIGHT - thumb_h)))
                        game.scroll_offset = -(ratio * max_off)

            if game.cheat_dragging_scrollbar and game.cheat_visible:
                cheat_top = 65
                cheat_h = SCREEN_HEIGHT - 95
                content_h = len(game.possible_words) * 24
                if content_h > 0:
                    thumb_h = max(30, (cheat_h / content_h) * cheat_h)
                    max_off = content_h - cheat_h
                    rel_y = my - cheat_top - thumb_h / 2
                    if cheat_h - thumb_h > 0:
                        ratio = max(0, min(1, rel_y / (cheat_h - thumb_h)))
                        game.cheat_scroll_offset = -(ratio * max_off)

        # ───────────────────────────────────────────────────────────────────
        # MOUSE WHEEL SCROLLING
        # ───────────────────────────────────────────────────────────────────
        elif event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()

            if game.cheat_visible and mx >= BASE_WIDTH:
                game.cheat_scroll_offset += event.y * 35
                cheat_h = SCREEN_HEIGHT - 95
                max_off = -max(0, len(game.possible_words) * 24 - cheat_h)
                game.cheat_scroll_offset = max(max_off, min(0, game.cheat_scroll_offset))
            else:
                game.scroll_offset += event.y * 35
                max_off = -max(0, len(game.found_words) * WORD_LINE_HEIGHT - WORDS_AREA_HEIGHT)
                game.scroll_offset = max(max_off, min(0, game.scroll_offset))

    # ───────────────────────────────────────────────────────────────────────
    # TIMER LOGIC
    # ───────────────────────────────────────────────────────────────────────
    time_left = game.get_time_left()

    # Countdown sounds (last 4 seconds)
    if game.timer_active and time_left in (1, 2, 3, 4):
        if time_left != game.last_countdown_second:
            ding_sound.play()
            game.last_countdown_second = time_left
    elif time_left == 0 and not game.timer_active:
        if game.last_countdown_second != 0:
            buzzer_sound.play()
            game.last_countdown_second = 0

    # ═══════════════════════════════════════════════════════════════════════
    # RENDERING
    # ═══════════════════════════════════════════════════════════════════════

    screen.fill(WHITE)

    # ───────────────────────────────────────────────────────────────────────
    # DRAW BOARD GRID
    # ───────────────────────────────────────────────────────────────────────
    grid_background = pygame.Rect(0, 0, GRID_WIDTH, GRID_SIZE * CELL_SIZE + 40)
    pygame.draw.rect(screen, BLACK, grid_background)

    grid_border = pygame.Rect(0, 0, GRID_WIDTH, GRID_SIZE * CELL_SIZE + 40)
    draw_rounded_rect(screen, BLACK, grid_border, border_radius=15, border_width=20, border_color=NAVY_BLUE)

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(col * CELL_SIZE + 20, row * CELL_SIZE + 20, CELL_SIZE, CELL_SIZE)
            pos = (row, col)

            if pos in game.selected_path_from_cheat:
                color = (255, 220, 100)
            elif pos in game.selected_path:
                color = YELLOW
            else:
                color = WHITE

            draw_rounded_rect(screen, color, rect, border_radius=15, border_width=2, border_color=GRAY)

            inner_rect = pygame.Rect(rect.x + 10, rect.y + 10, rect.width - 20, rect.height - 20)
            draw_rounded_rect(screen, color, inner_rect, border_radius=10, border_width=4, border_color=LIGHT_GRAY)

            letter = game.board[row * GRID_SIZE + col]
            text = font.render(letter, True, BLACK)
            screen.blit(text, text.get_rect(center=rect.center))

    # ───────────────────────────────────────────────────────────────────────
    # DRAW CHEAT PATH LINES
    # ───────────────────────────────────────────────────────────────────────
    if game.selected_path_from_cheat:
        for i in range(len(game.selected_path_from_cheat) - 1):
            r1, c1 = game.selected_path_from_cheat[i]
            r2, c2 = game.selected_path_from_cheat[i + 1]

            x1 = c1 * CELL_SIZE + CELL_SIZE // 2 + 20
            y1 = r1 * CELL_SIZE + CELL_SIZE // 2 + 20
            x2 = c2 * CELL_SIZE + CELL_SIZE // 2 + 20
            y2 = r2 * CELL_SIZE + CELL_SIZE // 2 + 20

            pygame.draw.line(screen, (0, 255, 32), (x1, y1), (x2, y2), 6)

    # ───────────────────────────────────────────────────────────────────────
    # DRAW SIDEBAR
    # ───────────────────────────────────────────────────────────────────────
    x = GRID_WIDTH + 20

    current = game.get_current_word()
    screen.blit(small_font.render("Word: " + current, True, BLACK), (x, 20))

    screen.blit(small_font.render("Found:", True, GREEN), (x, WORDS_AREA_Y - 20))

    area_rect = pygame.Rect(x - 10, WORDS_AREA_Y, WORDS_AREA_WIDTH + 20, WORDS_AREA_HEIGHT)
    pygame.draw.rect(screen, WHITE, area_rect)
    pygame.draw.rect(screen, GRAY, area_rect, 1)

    for i, (w, tile_count) in enumerate(game.found_words):
        y_pos = WORDS_AREA_Y + i * WORD_LINE_HEIGHT + game.scroll_offset
        if WORDS_AREA_Y <= y_pos <= WORDS_AREA_Y + WORDS_AREA_HEIGHT - WORD_LINE_HEIGHT:
            pts = GameState.calculate_score(tile_count)

            screen.blit(small_font.render(w, True, BLACK), (x + 5, y_pos))

            pts_text = small_font.render(str(pts), True, (100, 100, 100))
            screen.blit(pts_text, (x + WORDS_AREA_WIDTH - 40, y_pos))

    # ───────────────────────────────────────────────────────────────────────
    # DRAW MAIN SCROLLBAR
    # ───────────────────────────────────────────────────────────────────────
    if len(game.found_words) * WORD_LINE_HEIGHT > WORDS_AREA_HEIGHT:
        content_h = len(game.found_words) * WORD_LINE_HEIGHT
        max_scroll = content_h - WORDS_AREA_HEIGHT
        if content_h > 0 and max_scroll > 0:
            thumb_h = max(30, (WORDS_AREA_HEIGHT / content_h) * WORDS_AREA_HEIGHT)
            thumb_y = WORDS_AREA_Y + (-game.scroll_offset / max_scroll) * (WORDS_AREA_HEIGHT - thumb_h)
            sb_rect = pygame.Rect(scrollbar_x, thumb_y, scrollbar_width, thumb_h)

            color = SCROLLBAR_ACTIVE if sb_rect.collidepoint(pygame.mouse.get_pos()) or game.dragging_scrollbar else SCROLLBAR_COLOR
            pygame.draw.rect(screen, color, sb_rect)
            pygame.draw.rect(screen, BLACK, sb_rect, 1)

    # ───────────────────────────────────────────────────────────────────────
    # DRAW STATUS TEXT
    # ───────────────────────────────────────────────────────────────────────
    bottom_y = GRID_SIZE * CELL_SIZE + 70

    screen.blit(small_font.render(f"Score: {game.score}", True, BLACK), (x, bottom_y))
    screen.blit(small_font.render(f"Words possible: {len(game.possible_words)}",
                                  True, (90, 90, 140)), (x, bottom_y + 60))

    timer_str = f"Time: {time_left // 60:02d}:{time_left % 60:02d}"
    timer_color = RED if time_left <= 30 and game.timer_active else BLACK
    screen.blit(small_font.render(timer_str, True, timer_color), (x, bottom_y + 30))

    # ───────────────────────────────────────────────────────────────────────
    # DRAW CHEAT PANEL
    # ───────────────────────────────────────────────────────────────────────
    cheat_text = "Hide Cheat" if game.cheat_visible else "Cheat"
    cheat_color = DARK_BLUE if game.cheat_visible else RED

    if game.cheat_visible:
        cheat_x = BASE_WIDTH + 15

        pygame.draw.rect(screen, (235, 235, 255),
                        (BASE_WIDTH, 0, CHEAT_PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(screen, GRAY, (BASE_WIDTH, 0), (BASE_WIDTH, SCREEN_HEIGHT), 2)

        screen.blit(small_font.render("Possible Words", True, DARK_BLUE), (cheat_x, 25))

        cheat_top = 65
        cheat_h = SCREEN_HEIGHT - 95
        cheat_area = pygame.Rect(BASE_WIDTH + 5, cheat_top, CHEAT_PANEL_WIDTH - 10, cheat_h)
        pygame.draw.rect(screen, WHITE, cheat_area)
        pygame.draw.rect(screen, GRAY, cheat_area, 1)

        line_h = 24
        total = len(game.possible_words) * line_h

        for i, word in enumerate(game.possible_words):
            y = cheat_top + i * line_h + game.cheat_scroll_offset
            if cheat_top <= y <= cheat_top + cheat_h - line_h:
                color = (0, 100, 180) if word == game.selected_cheat_word else BLACK
                screen.blit(small_font.render(word, True, color), (cheat_x, y))

        if total > cheat_h and total > 0:
            max_scroll = total - cheat_h
            thumb_h = max(30, cheat_h / total * cheat_h)
            thumb_y = cheat_top + (-game.cheat_scroll_offset / max_scroll) * (cheat_h - thumb_h)
            sb_rect = pygame.Rect(BASE_WIDTH + CHEAT_PANEL_WIDTH - 20, thumb_y, 14, thumb_h)

            color = SCROLLBAR_ACTIVE if sb_rect.collidepoint(pygame.mouse.get_pos()) or game.cheat_dragging_scrollbar else SCROLLBAR_COLOR
            pygame.draw.rect(screen, color, sb_rect)
            pygame.draw.rect(screen, BLACK, sb_rect, 1)

    # ───────────────────────────────────────────────────────────────────────
    # DRAW BUTTONS
    # ───────────────────────────────────────────────────────────────────────
    buttons = [
        (submit_rect,       "Submit Word",       BLUE),
        (timer_toggle_rect, "Timer Start/Stop",  DARK_BLUE if game.timer_active else BLUE),
        (timer_reset_rect,  "Reset Timer",       BLUE),
        (reshuffle_rect,    "Re-shuffle",        BLUE),
        (cheat_rect,        cheat_text,          cheat_color)
    ]

    mouse_pos = pygame.mouse.get_pos()
    for rect, text, base_color in buttons:
        if rect.collidepoint(mouse_pos):
            if rect == cheat_rect and base_color == RED:
                color = (180, 30, 30)
            elif base_color == DARK_BLUE:
                color = (40, 80, 170)
            else:
                color = DARK_BLUE
        else:
            color = base_color

        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BLACK, rect, 3)

        btn = button_font.render(text, True, WHITE)
        screen.blit(btn, btn.get_rect(center=rect.center))

    # ───────────────────────────────────────────────────────────────────────
    # FLIP DISPLAY AND LIMIT FRAMERATE
    # ───────────────────────────────────────────────────────────────────────
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
