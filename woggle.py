# ═══════════════════════════════════════════════════════════════════════════
# Woggle 1.2.5 - An Oddly Familiar Word Game
# by no1453@gmail.com
# 2026.01.19
# A Boggle-style word game with timer, scoring, and cheat mode
# FIXED: Visual style of grid corners on cubes, cube face
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
cubes = [
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
try:
    with open("words", "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().upper()
            if word and 3 <= len(word) <= 16:  # Only accept words 3-16 letters
                dictionary.add(word)
except FileNotFoundError:
    print("Warning: 'words' file not found.")

# Build prefix set for efficient word search pruning
# This dramatically speeds up the DFS search by eliminating impossible paths early
prefixes = set()
for word in dictionary:
    for i in range(1, len(word) + 1):
        prefixes.add(word[:i])

# ───────────────────────────────────────────────────────────────────────────
# BOARD GENERATION
# Functions to create and manage the game board.
# ───────────────────────────────────────────────────────────────────────────

def generate_board():
    """
    Generate a random 4x4 Boggle board.
    Shuffles the dice, then picks one random face from each die.
    Returns a flat list of 16 letters.
    """
    shuffled = cubes[:]
    random.shuffle(shuffled)
    return [random.choice(cube) for cube in shuffled]

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

# ───────────────────────────────────────────────────────────────────────────
# GAME LOGIC FUNCTIONS
# Core functions for validating moves, words, and adjacency on the board.
# ───────────────────────────────────────────────────────────────────────────

def is_adjacent(pos1, pos2):
    """
    Check if two board positions are adjacent (including diagonals).
    Plays buzzer sound if positions are not adjacent.
    
    Args:
        pos1, pos2: Tuples of (row, col) coordinates
    
    Returns:
        True if positions are adjacent, False otherwise
    """
    r1, c1 = pos1
    r2, c2 = pos2
    retval = max(abs(r1 - r2), abs(c1 - c2)) == 1 and pos1 != pos2
    if not retval:
        buzzer_sound.play()
    return retval

def is_valid_word(word, board, path):
    """
    Validate that a word is legal according to Boggle rules.
    
    Checks:
    - Word is at least 3 letters
    - Word exists in dictionary
    - Path length matches word length (accounting for "QU")
    - All positions in path are adjacent
    
    Args:
        word: The word string to validate
        board: The current board state (flat list of letters)
        path: List of (row, col) positions forming the word
    
    Returns:
        True if word is valid, False otherwise
    """
    if len(word) < 3 or word not in dictionary:
        return False
    
    # Account for "QU" counting as one letter but two characters
    word_length = len(word)
    if word.startswith("QU"):
        word_length -= 1
    
    if len(path) != word_length:
        return False
    
    # Verify all positions are adjacent
    for i in range(1, len(path)):
        if not is_adjacent(path[i-1], path[i]):
            return False
    
    return True

# ───────────────────────────────────────────────────────────────────────────
# WORD FINDING ALGORITHMS
# Efficient algorithms to find all possible words on the board and paths for
# specific words, used for cheat mode and validation.
# ───────────────────────────────────────────────────────────────────────────

def find_all_possible_words(board, dictionary):
    """
    Find all valid words that can be formed on the current board.
    Uses depth-first search with prefix pruning for efficiency.
    
    Args:
        board: Flat list of 16 letters
        dictionary: Set of valid words
    
    Returns:
        Sorted list of all possible words
    """
    GRID_SIZE = 4
    board_flat = board

    def get_letter(idx):
        """Get letter at index, converting 'Qu' to 'QU'"""
        return "QU" if board_flat[idx] == "Qu" else board_flat[idx]

    def dfs(pos, visited, current_word):
        """
        Depth-first search to find words starting from position.
        
        Args:
            pos: Current position index (0-15)
            visited: Set of already-visited positions
            current_word: Word built so far
        """
        # Limit search depth to prevent infinite recursion
        if len(current_word) > 16:
            return
        
        # Add current letter to word
        letter = get_letter(pos)
        current_word += letter
        
        # Prune: if no dictionary word starts with this prefix, stop searching
        if current_word not in prefixes:
            return
        
        # If we found a valid word, add it to results
        if len(current_word) >= 3 and current_word in dictionary:
            found.add(current_word)
        
        # Explore all adjacent positions
        r, c = divmod(pos, GRID_SIZE)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == dc == 0:  # Skip current position
                    continue
                    
                nr, nc = r + dr, c + dc
                if 0 <= nr < 4 and 0 <= nc < 4:
                    new_pos = nr * 4 + nc
                    if new_pos not in visited:
                        visited.add(new_pos)
                        dfs(new_pos, visited, current_word)
                        visited.remove(new_pos)  # Backtrack

    # Try starting from each position on the board
    found = set()
    for start_pos in range(16):
        visited = {start_pos}
        dfs(start_pos, visited, "")
    
    return sorted(found)

def find_path_for_word(target, board):
    """
    Find a valid path on the board that spells the target word.
    Used for the cheat mode to show where words can be found.
    
    Args:
        target: The word to find
        board: Current board state (flat list of letters)
    
    Returns:
        List of (row, col) positions forming the word, or None if not found
    """
    target = target.upper()
    GRID_SIZE = 4

    def get_letter(idx):
        """Get letter at index, converting 'Qu' to 'QU'"""
        l = board[idx]
        return "QU" if l == "Qu" else l

    def dfs(pos, path, current):
        """
        Depth-first search to find path for target word.
        
        Args:
            pos: Current position index
            path: List of (row, col) positions visited so far
            current: Word built so far
        
        Returns:
            Complete path if word found, None otherwise
        """
        # Found the complete word!
        if current == target:
            return path[:]
        
        # Word is already too long
        if len(current) >= len(target):
            return None
        
        # Try all adjacent positions
        r, c = divmod(pos, GRID_SIZE)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == dc == 0:
                    continue
                    
                nr, nc = r + dr, c + dc
                if 0 <= nr < 4 and 0 <= nc < 4:
                    np = nr * 4 + nc
                    
                    # Don't revisit positions
                    if np not in {p[0] * 4 + p[1] for p in path}:
                        next_l = get_letter(np)
                        new = current + next_l
                        
                        # Only continue if we're still on track
                        if target.startswith(new):
                            path.append((nr, nc))
                            res = dfs(np, path, new)
                            if res:
                                return res
                            path.pop()  # Backtrack
        
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

# ═══════════════════════════════════════════════════════════════════════════
# GAME CONSTANTS AND SETUP
# Define dimensions, colors, fonts, and other constants used throughout the game.
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

# Fonts for different text sizes in the UI
font = pygame.font.SysFont(None, 60)          # Large font for board letters
small_font = pygame.font.SysFont(None, 32)    # Small font for UI text
button_font = pygame.font.SysFont(None, 36)   # Medium font for buttons

# ───────────────────────────────────────────────────────────────────────────
# BUTTON DEFINITIONS
# Pre-defined rectangles for all interactive buttons in the UI.
# ───────────────────────────────────────────────────────────────────────────
submit_rect      = pygame.Rect(0, GRID_SIZE * CELL_SIZE + 40,      GRID_WIDTH, 60)
timer_toggle_rect = pygame.Rect(0, GRID_SIZE * CELL_SIZE + 100, GRID_WIDTH // 2, 60)
timer_reset_rect  = pygame.Rect(GRID_WIDTH // 2, GRID_SIZE * CELL_SIZE + 100, GRID_WIDTH // 2, 60)
reshuffle_rect    = pygame.Rect(0, GRID_SIZE * CELL_SIZE + 160, GRID_WIDTH // 2, 60)
cheat_rect        = pygame.Rect(GRID_WIDTH // 2, GRID_SIZE * CELL_SIZE + 160, GRID_WIDTH // 2, 60)

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
    
    # Show for ~2 seconds, allow early exit
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

# Now create the *normal* main window with title bar

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
# GAME STATE VARIABLES
# Variables tracking the current state of the game, including board, scores,
# timer, and UI interactions.
# ───────────────────────────────────────────────────────────────────────────

# Board and word tracking
board = generate_board()
selected_path = []           # Current word being built by user
found_words = []             # List of (word, tile_count) tuples for found words
score = 0                    # Current score

# Timer state
timer_active = False         # Is timer currently running?
timer_start = 0              # Time when timer was started
total_elapsed = 0            # Total elapsed time (for pause/resume)
TIME_LIMIT = 180             # 3 minutes in seconds

# Found words panel scrolling
scroll_offset = 0
WORD_LINE_HEIGHT = 28
WORDS_AREA_Y = 70
WORDS_AREA_HEIGHT = 352
WORDS_AREA_WIDTH = SIDE_PANEL - 40
scrollbar_width = 10
scrollbar_padding = 8
dragging_scrollbar = False

# Countdown sound tracking (to play once per second)
last_countdown_second = -1

# Cheat mode state
cheat_visible = False              # Is cheat panel currently shown?
cheat_scroll_offset = 0            # Scroll position in cheat list
cheat_dragging_scrollbar = False   # Is user dragging cheat scrollbar?
selected_cheat_word = None         # Currently selected word in cheat list
selected_path_from_cheat = []      # Path to show for selected cheat word

# Possible words cache
possible_words = []

def update_possible_words():
    """Regenerate the list of all possible words for current board"""
    global possible_words
    possible_words = find_all_possible_words(board, dictionary)

# Generate initial word list
update_possible_words()

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
            
            # Only process left mouse button (prevents mousewheel clicks from selecting)
            if event.button != 1:
                continue

            # ───────────────────────────────────────────────────────────────
            # BOARD LETTER SELECTION
            # Click letters to build a word by selecting adjacent positions.
            # ───────────────────────────────────────────────────────────────
            if mx < GRID_WIDTH and my < GRID_SIZE * CELL_SIZE:
                col = mx // CELL_SIZE
                row = my // CELL_SIZE
                pos = (row, col)
                
                if not selected_path:
                    # Start new word
                    selected_path = [pos]
                elif pos == selected_path[0]:
                    # Clicked first letter again - clear selection
                    selected_path = []
                elif pos not in selected_path and is_adjacent(selected_path[-1], pos):
                    # Add adjacent letter to word
                    selected_path.append(pos)

            # ───────────────────────────────────────────────────────────────
            # SUBMIT WORD BUTTON
            # Validate and score the currently selected word if valid.
            # ───────────────────────────────────────────────────────────────
            if submit_rect.collidepoint(mx, my) and selected_path:
                # Build word string from selected path
                word = "".join(board[r*GRID_SIZE + c].replace("Qu", "QU") 
                              for r, c in selected_path).upper()
                
                # Check if word already found (comparing just the word string)
                found_word_strings = [w for w, tc in found_words]
                
                if is_valid_word(word, board, selected_path) and word not in found_word_strings:
                    # Valid new word! Store word with its tile count
                    tile_count = len(selected_path)
                    found_words.append((word, tile_count))
                    
                    # Calculate score based on number of tiles used (path length), not string length
                    # This ensures "Qu" counts as one tile for scoring purposes
                    l = tile_count
                    score += 1 if l <= 4 else 2 if l == 5 else 3 if l == 6 else 5 if l == 7 else 11
                    
                    # Auto-scroll to show new word at bottom
                    scroll_offset = -max(0, len(found_words) * WORD_LINE_HEIGHT - WORDS_AREA_HEIGHT)
                    ding_sound.play()
                else:
                    # Invalid word or already found
                    buzzer_sound.play()
                
                selected_path = []

            # ───────────────────────────────────────────────────────────────
            # TIMER START/STOP BUTTON
            # Toggle timer on/off, tracking elapsed time for pauses.
            # ───────────────────────────────────────────────────────────────
            if timer_toggle_rect.collidepoint(mx, my):
                if timer_active:
                    # Pause timer - save elapsed time
                    total_elapsed += time.time() - timer_start
                    timer_active = False
                else:
                    # Start/resume timer
                    timer_start = time.time()
                    timer_active = True
                ding_sound.play()

            # ───────────────────────────────────────────────────────────────
            # RESET TIMER BUTTON
            # Clear timer and current selection.
            # ───────────────────────────────────────────────────────────────
            if timer_reset_rect.collidepoint(mx, my):
                timer_active = False
                total_elapsed = 0
                timer_start = 0
                selected_path = []
                ding_sound.play()

            # ───────────────────────────────────────────────────────────────
            # RE-SHUFFLE BUTTON
            # Generate new board and reset all game state.
            # ───────────────────────────────────────────────────────────────
            if reshuffle_rect.collidepoint(mx, my):
                board = generate_board()
                selected_path = []
                found_words = []
                score = 0
                timer_active = False
                timer_start = 0
                total_elapsed = 0
                scroll_offset = 0
                cheat_scroll_offset = 0
                selected_cheat_word = None
                selected_path_from_cheat = []
                update_possible_words()
                ding_sound.play()

            # ───────────────────────────────────────────────────────────────
            # CHEAT BUTTON
            # Toggle visibility of cheat panel showing all possible words.
            # ───────────────────────────────────────────────────────────────
            if cheat_rect.collidepoint(mx, my):
                cheat_visible = not cheat_visible
                
                if cheat_visible:
                    # Show cheat panel - expand window
                    screen = pygame.display.set_mode((BASE_WIDTH + CHEAT_PANEL_WIDTH, SCREEN_HEIGHT))
                    pygame.display.set_caption("Woggle – An Oddly Familiar Word Game - Cheat Mode")
                else:
                    # Hide cheat panel - shrink window
                    screen = pygame.display.set_mode((BASE_WIDTH, SCREEN_HEIGHT))
                    pygame.display.set_caption("Woggle - An Oddly Familiar Word Game")
                    selected_cheat_word = None
                    selected_path_from_cheat = []
                
                ding_sound.play()

            # ───────────────────────────────────────────────────────────────
            # MAIN PANEL SCROLLBAR
            # Detect if user clicked on scrollbar thumb to start dragging.
            # ───────────────────────────────────────────────────────────────
            if len(found_words) * WORD_LINE_HEIGHT > WORDS_AREA_HEIGHT:
                content_h = len(found_words) * WORD_LINE_HEIGHT
                if content_h > 0:  # Guard against division by zero
                    thumb_h = max(30, (WORDS_AREA_HEIGHT / content_h) * WORDS_AREA_HEIGHT)
                    thumb_y = WORDS_AREA_Y + (-scroll_offset / content_h) * (WORDS_AREA_HEIGHT - thumb_h)
                    sb_rect = pygame.Rect(GRID_WIDTH + WORDS_AREA_WIDTH + scrollbar_padding, 
                                         thumb_y, scrollbar_width, thumb_h)
                    if sb_rect.collidepoint(mx, my):
                        dragging_scrollbar = True

            # ───────────────────────────────────────────────────────────────
            # CHEAT PANEL SCROLLBAR
            # Detect if user clicked on cheat scrollbar thumb to start dragging.
            # ───────────────────────────────────────────────────────────────
            if cheat_visible:
                content_h = len(possible_words) * 24
                visible_h = SCREEN_HEIGHT - 100
                if content_h > visible_h and content_h > 0:  # Guard against division by zero
                    thumb_h = max(30, (visible_h / content_h) * visible_h)
                    thumb_y = 60 + (-cheat_scroll_offset / content_h) * (visible_h - thumb_h)
                    sb_rect = pygame.Rect(BASE_WIDTH + CHEAT_PANEL_WIDTH - 20, thumb_y, 14, thumb_h)
                    if sb_rect.collidepoint(mx, my):
                        cheat_dragging_scrollbar = True
                        continue  # Don't process word click if clicking scrollbar

            # ───────────────────────────────────────────────────────────────
            # CHEAT WORD SELECTION
            # Click a word in cheat list to highlight its path on board.
            # ───────────────────────────────────────────────────────────────
            if cheat_visible and mx >= BASE_WIDTH and not cheat_dragging_scrollbar:
                cheat_top = 70
                line_h = 24
                cheat_h = SCREEN_HEIGHT - 95
                
                # Only select if clicking in the word area (not scrollbar)
                cheat_area = pygame.Rect(BASE_WIDTH + 5, cheat_top, CHEAT_PANEL_WIDTH - 30, cheat_h)
                if cheat_area.collidepoint(mx, my):
                    for i, word in enumerate(possible_words):
                        y = cheat_top + i * line_h + cheat_scroll_offset
                        if cheat_top <= y <= cheat_top + cheat_h - line_h:
                            if y <= my <= y + line_h:
                                # Toggle selection: clicking selected word unselects it
                                if word == selected_cheat_word:
                                    selected_cheat_word = None
                                    selected_path_from_cheat = []
                                    ding_sound.play()
                                else:
                                    # Find and highlight path for this word
                                    path = find_path_for_word(word, board)
                                    if path:
                                        selected_cheat_word = word
                                        selected_path_from_cheat = path
                                        ding_sound.play()
                                break

        # ───────────────────────────────────────────────────────────────────
        # MOUSE BUTTON RELEASE
        # Stop dragging scrollbars when mouse button is released.
        # ───────────────────────────────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging_scrollbar = False
            cheat_dragging_scrollbar = False

        # ───────────────────────────────────────────────────────────────────
        # MOUSE MOTION (DRAGGING)
        # Update scroll positions while dragging scrollbars.
        # ───────────────────────────────────────────────────────────────────
        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            
            # Main panel scrollbar dragging
            if dragging_scrollbar:
                content_h = len(found_words) * WORD_LINE_HEIGHT
                if content_h > 0:  # Guard against division by zero
                    thumb_h = max(30, (WORDS_AREA_HEIGHT / content_h) * WORDS_AREA_HEIGHT)
                    max_off = content_h - WORDS_AREA_HEIGHT
                    rel_y = my - WORDS_AREA_Y - thumb_h / 2
                    if WORDS_AREA_HEIGHT - thumb_h > 0:  # Additional guard
                        ratio = max(0, min(1, rel_y / (WORDS_AREA_HEIGHT - thumb_h)))
                        scroll_offset = -(ratio * max_off)
            
            # Cheat panel scrollbar dragging
            if cheat_dragging_scrollbar and cheat_visible:
                content_h = len(possible_words) * 24
                visible_h = SCREEN_HEIGHT - 100
                if content_h > 0:  # Guard against division by zero
                    thumb_h = max(30, (visible_h / content_h) * visible_h)
                    max_off = content_h - visible_h
                    rel_y = my - 60 - thumb_h / 2
                    if visible_h - thumb_h > 0:  # Additional guard
                        ratio = max(0, min(1, rel_y / (visible_h - thumb_h)))
                        cheat_scroll_offset = -(ratio * max_off)

        # ───────────────────────────────────────────────────────────────────
        # MOUSE WHEEL SCROLLING
        # Scroll found words or cheat list with mouse wheel based on mouse position.
        # ───────────────────────────────────────────────────────────────────
        elif event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            
            # Scroll cheat panel if mouse is over it
            if cheat_visible and mx >= BASE_WIDTH:
                cheat_scroll_offset += event.y * 35
                max_off = -max(0, len(possible_words) * 24 - (SCREEN_HEIGHT - 100))
                cheat_scroll_offset = max(max_off, min(0, cheat_scroll_offset))
            else:
                # Scroll main found words panel
                scroll_offset += event.y * 35
                max_off = -max(0, len(found_words) * WORD_LINE_HEIGHT - WORDS_AREA_HEIGHT)
                scroll_offset = max(max_off, min(0, scroll_offset))

    # ───────────────────────────────────────────────────────────────────────
    # TIMER LOGIC
    # Calculate remaining time and play countdown sounds in the last few seconds.
    # ───────────────────────────────────────────────────────────────────────
    time_left = TIME_LIMIT
    
    if timer_active:
        # Timer is running - calculate time left
        current_elapsed = time.time() - timer_start + total_elapsed
        time_left = max(0, TIME_LIMIT - int(current_elapsed))
        if time_left <= 0:
            timer_active = False
    else:
        # Timer is paused - show remaining time based on total elapsed
        time_left = max(0, TIME_LIMIT - int(total_elapsed))

    # Countdown sounds (last 4 seconds)
    if timer_active and time_left in (1, 2, 3, 4):
        if time_left != last_countdown_second:
            ding_sound.play()
            last_countdown_second = time_left
    elif time_left == 0 and not timer_active:
        # Time's up - play buzzer once
        if last_countdown_second != 0:
            buzzer_sound.play()
            last_countdown_second = 0

    # ═══════════════════════════════════════════════════════════════════════
    # RENDERING
    # Draw all game elements to the screen, including board, UI, and panels.
    # ═══════════════════════════════════════════════════════════════════════
    
    screen.fill(WHITE)

    # ───────────────────────────────────────────────────────────────────────
    # DRAW BOARD GRID
    # 4x4 grid of letters with highlighting for selected/cheat paths.
    # ───────────────────────────────────────────────────────────────────────

    # Draw black background for the grid area to fill corner gaps
    grid_background = pygame.Rect(0, 0, GRID_WIDTH, GRID_SIZE * CELL_SIZE + 40)
    pygame.draw.rect(screen, BLACK, grid_background)

    # Draw 20 pixel navy blue rounded rectangle border around the entire grid
    grid_border = pygame.Rect(0, 0, GRID_WIDTH, GRID_SIZE * CELL_SIZE + 40)
    draw_rounded_rect(screen, BLACK, grid_border, border_radius=15, border_width=20, border_color=NAVY_BLUE)

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(col * CELL_SIZE + 20, row * CELL_SIZE + 20, CELL_SIZE, CELL_SIZE)
            pos = (row, col)

            # Choose cell color based on selection state
            if pos in selected_path_from_cheat:
                color = (255, 220, 100)  # Orange tint for cheat path
            elif pos in selected_path:
                color = YELLOW           # Yellow for user selection
            else:
                color = WHITE            # Default white

            # Draw rounded rectangle with border
            draw_rounded_rect(screen, color, rect, border_radius=15, border_width=2, border_color=GRAY)

            # Draw second smaller rounded rectangle, 10 pixels inset on each side
            inner_rect = pygame.Rect(rect.x + 10, rect.y + 10, rect.width - 20, rect.height - 20)
            draw_rounded_rect(screen, color, inner_rect, border_radius=10, border_width=4, border_color=LIGHT_GRAY)

            # Draw letter in center of cell
            letter = board[row * GRID_SIZE + col]
            display = "QU" if letter == "Qu" else letter
            text = font.render(display, True, BLACK)
            screen.blit(text, text.get_rect(center=rect.center))

    # ───────────────────────────────────────────────────────────────────────
    # DRAW CHEAT PATH LINES
    # Green lines connecting letters in selected cheat word.
    # ───────────────────────────────────────────────────────────────────────
    if selected_path_from_cheat:
        for i in range(len(selected_path_from_cheat) - 1):
            r1, c1 = selected_path_from_cheat[i]
            r2, c2 = selected_path_from_cheat[i + 1]

            # Calculate center points of cells (offset by 20 for grid border)
            x1 = c1 * CELL_SIZE + CELL_SIZE // 2 + 20
            y1 = r1 * CELL_SIZE + CELL_SIZE // 2 + 20
            x2 = c2 * CELL_SIZE + CELL_SIZE // 2 + 20
            y2 = r2 * CELL_SIZE + CELL_SIZE // 2 + 20

            pygame.draw.line(screen, (0, 255, 32), (x1, y1), (x2, y2), 6)

    # ───────────────────────────────────────────────────────────────────────
    # DRAW SIDEBAR
    # Current word, found words list, score, and timer.
    # ───────────────────────────────────────────────────────────────────────
    x = GRID_WIDTH + 20
    
    # Current word being built
    current = "".join(board[r*GRID_SIZE + c].replace("Qu", "QU") 
                     for r, c in selected_path)
    screen.blit(small_font.render("Word: " + current.upper(), True, BLACK), (x, 20))
    
    # "Found:" header
    screen.blit(small_font.render("Found:", True, GREEN), (x, WORDS_AREA_Y - 20))

    # Found words scrollable area
    area_rect = pygame.Rect(x - 10, WORDS_AREA_Y, WORDS_AREA_WIDTH + 20, WORDS_AREA_HEIGHT)
    pygame.draw.rect(screen, WHITE, area_rect)
    pygame.draw.rect(screen, GRAY, area_rect, 1)

    # Draw found words list with point values
    for i, (w, tile_count) in enumerate(found_words):
        y_pos = WORDS_AREA_Y + i * WORD_LINE_HEIGHT + scroll_offset
        if WORDS_AREA_Y <= y_pos <= WORDS_AREA_Y + WORDS_AREA_HEIGHT - WORD_LINE_HEIGHT:
            # Calculate point value based on tile count (not string length)
            pts = 1 if tile_count <= 4 else 2 if tile_count == 5 else 3 if tile_count == 6 else 5 if tile_count == 7 else 11
            
            # Display word on left
            screen.blit(small_font.render(w, True, BLACK), (x + 5, y_pos))
            
            # Display points right-justified in gray
            pts_text = small_font.render(str(pts), True, (100, 100, 100))
            screen.blit(pts_text, (x + WORDS_AREA_WIDTH - 25, y_pos))

    # ───────────────────────────────────────────────────────────────────────
    # DRAW MAIN SCROLLBAR
    # Scrollbar for found words list, visible only if content overflows.
    # ───────────────────────────────────────────────────────────────────────
    if len(found_words) * WORD_LINE_HEIGHT > WORDS_AREA_HEIGHT:
        content_h = len(found_words) * WORD_LINE_HEIGHT
        if content_h > 0:  # Guard against division by zero
            thumb_h = max(30, (WORDS_AREA_HEIGHT / content_h) * WORDS_AREA_HEIGHT)
            thumb_y = WORDS_AREA_Y + (-scroll_offset / content_h) * (WORDS_AREA_HEIGHT - thumb_h)
            sb_rect = pygame.Rect(GRID_WIDTH + WORDS_AREA_WIDTH + scrollbar_padding, 
                                 thumb_y, scrollbar_width, thumb_h)
            
            # Highlight scrollbar on hover or drag
            color = SCROLLBAR_ACTIVE if sb_rect.collidepoint(pygame.mouse.get_pos()) or dragging_scrollbar else SCROLLBAR_COLOR
            pygame.draw.rect(screen, color, sb_rect)
            pygame.draw.rect(screen, BLACK, sb_rect, 1)
        pygame.draw.rect(screen, BLACK, sb_rect, 1)

    # ───────────────────────────────────────────────────────────────────────
    # DRAW STATUS TEXT
    # Score, possible words count, and timer (color changes when low).
    # ───────────────────────────────────────────────────────────────────────
    bottom_y = GRID_SIZE * CELL_SIZE + 70
    
    screen.blit(small_font.render(f"Score: {score}", True, BLACK), (x, bottom_y))
    screen.blit(small_font.render(f"Words possible: {len(possible_words)}", 
                                  True, (90, 90, 140)), (x, bottom_y + 60))
    
    # Timer display (red when under 30 seconds and running)
    timer_str = f"Time: {time_left // 60:02d}:{time_left % 60:02d}"
    timer_color = RED if time_left <= 30 and timer_active else BLACK
    screen.blit(small_font.render(timer_str, True, timer_color), (x, bottom_y + 30))

    # ───────────────────────────────────────────────────────────────────────
    # DRAW CHEAT PANEL
    # Side panel showing all possible words (if enabled), with scrolling.
    # ───────────────────────────────────────────────────────────────────────
    cheat_text = "Hide Cheat" if cheat_visible else "Cheat"
    cheat_color = DARK_BLUE if cheat_visible else RED

    if cheat_visible:
        cheat_x = BASE_WIDTH + 15
        
        # Background panel
        pygame.draw.rect(screen, (235, 235, 255), 
                        (BASE_WIDTH, 0, CHEAT_PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(screen, GRAY, (BASE_WIDTH, 0), (BASE_WIDTH, SCREEN_HEIGHT), 2)

        # Header
        screen.blit(small_font.render("Possible Words", True, DARK_BLUE), (cheat_x, 25))

        # Scrollable word list area
        cheat_top = 65
        cheat_h = SCREEN_HEIGHT - 95
        cheat_area = pygame.Rect(BASE_WIDTH + 5, cheat_top, CHEAT_PANEL_WIDTH - 10, cheat_h)
        pygame.draw.rect(screen, WHITE, cheat_area)
        pygame.draw.rect(screen, GRAY, cheat_area, 1)

        line_h = 24
        total = len(possible_words) * line_h

        # Draw visible words
        for i, word in enumerate(possible_words):
            y = cheat_top + i * line_h + cheat_scroll_offset
            if cheat_top <= y <= cheat_top + cheat_h - line_h:
                # Highlight selected word in blue
                color = (0, 100, 180) if word == selected_cheat_word else BLACK
                screen.blit(small_font.render(word, True, color), (cheat_x, y))

        # Cheat panel scrollbar (if needed)
        if total > cheat_h and total > 0:  # Guard against division by zero
            thumb_h = max(30, cheat_h / total * cheat_h)
            thumb_y = cheat_top + (-cheat_scroll_offset / total) * (cheat_h - thumb_h)
            sb_rect = pygame.Rect(BASE_WIDTH + CHEAT_PANEL_WIDTH - 20, thumb_y, 14, thumb_h)
            
            # Highlight scrollbar on hover or drag
            color = SCROLLBAR_ACTIVE if sb_rect.collidepoint(pygame.mouse.get_pos()) or cheat_dragging_scrollbar else SCROLLBAR_COLOR
            pygame.draw.rect(screen, color, sb_rect)
            pygame.draw.rect(screen, BLACK, sb_rect, 1)

    # ───────────────────────────────────────────────────────────────────────
    # DRAW BUTTONS
    # All interactive buttons with hover effects for visual feedback.
    # ───────────────────────────────────────────────────────────────────────
    buttons = [
        (submit_rect,       "Submit Word",       BLUE),
        (timer_toggle_rect, "Timer Start/Stop",  DARK_BLUE if timer_active else BLUE),
        (timer_reset_rect,  "Reset Timer",       BLUE),
        (reshuffle_rect,    "Re-shuffle",        BLUE),
        (cheat_rect,        cheat_text,          cheat_color)
    ]

    mouse_pos = pygame.mouse.get_pos()
    for rect, text, base_color in buttons:
        # Determine button color based on hover state
        if rect.collidepoint(mouse_pos):
            if rect == cheat_rect and base_color == RED:
                color = (180, 30, 30)   # Dark red for red cheat button
            elif base_color == DARK_BLUE:
                color = (40, 80, 170)   # Even darker blue for dark blue buttons
            else:
                color = DARK_BLUE       # Dark blue for normal blue buttons
        else:
            color = base_color

        # Draw button background and border
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BLACK, rect, 3)
        
        # Draw button text centered
        btn = button_font.render(text, True, WHITE)
        screen.blit(btn, btn.get_rect(center=rect.center))

    # ───────────────────────────────────────────────────────────────────────
    # FLIP DISPLAY AND LIMIT FRAMERATE
    # Update the display and cap the frame rate to 60 FPS for smooth performance.
    # ───────────────────────────────────────────────────────────────────────
    pygame.display.flip()
    clock.tick(60)  # 60 FPS

pygame.quit()
