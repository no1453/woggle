# Woggle

A Boggle-style single-player word game built with Python and Pygame.

## Description

Woggle is a word-finding game where you create words by connecting adjacent letters on a 4×4 grid. Race against the clock to find as many valid words as possible, or take your time in untimed mode to discover every word on the board.

## Requirements

- Python 3.x
- pygame
- numpy

Install dependencies with:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pygame numpy
```

## Setup

1. Clone or download this repository
2. Place a dictionary file named `words` in the same directory as `woggle.py`,
   One comes with the repo, also needed are the icon and splash files.
   - The dictionary should contain one word per line
   - Only words with 3 or more letters will be used
   - Words should be in plain text format

## How to Play

Run the game with:
```bash
python woggle.py
```

### Basic Rules

- Find words by clicking adjacent letters on the grid (including diagonals)
- Words must be at least 3 letters long
- Each letter tile can only be used once per word
- Letters must be adjacent to continue building a word
- Click "Submit Word" to submit your word

### Scoring

Points are awarded based on word length (measured in tiles, not letters):
- 3-4 tiles: 1 point
- 5 tiles: 2 points
- 6 tiles: 3 points
- 7 tiles: 5 points
- 8+ tiles: 11 points

Note: "Qu" counts as one tile but two letters.

### Controls

**Mouse:**
- Click letters to build words
- Click first selected letter to deselect all
- Scroll in the word list area to view all found words
- Click and drag scrollbars for precise control

**Buttons:**
- **Submit Word** - Submit your current word for scoring
- **Timer Start/Stop** - Toggle the 3-minute countdown timer
- **Reset Timer** - Reset timer back to 3:00
- **Re-shuffle** - Generate a new random board
- **Cheat** - Toggle the cheat panel (shows all possible words)

### Visual Feedback

- **White tiles** - Unselected letters
- **Yellow tiles** - Your current word selection
- **Tan tiles** - Highlighted path from cheat panel
- **Red timer** - Less than 30 seconds remaining
- **Green lines** - Path visualization when using cheat mode

### Audio

The game includes procedurally generated sound effects:
- Pleasant "ding" sound for valid word submissions
- Buzzer sound for invalid moves or word attempts

## Cheat Mode

Click the "Cheat" button to reveal all possible words on the current board. In cheat mode:
- All valid words are listed in the right panel
- Click any word to see its path highlighted on the board in green
- The cheat panel can be scrolled to view all words
- Click "Hide Cheat" to close the panel

## Features

- Standard Boggle dice configuration for authentic gameplay
- 3-minute timer with visual warnings
- Untimed practice mode
- Score tracking
- Scrollable word lists for viewing all found words
- Interactive cheat mode for learning
- Sound effects for feedback
- Smooth scrolling with mouse wheel and draggable scrollbars

## Project Structure

```
woggle/
├── woggle.py          # Main game file with GameState class
├── test_woggle.py     # Unit tests for game logic
├── requirements.txt   # Python dependencies
├── words              # Dictionary file (370K+ words)
├── woggle.ico         # Application icon
├── woggleSplash.png   # Splash screen image
└── README.md          # This file
```

## Testing

Run the unit tests with:
```bash
python -m unittest test_woggle -v
```

The test suite includes 34 tests covering:
- Adjacency checking (horizontal, vertical, diagonal)
- Scoring calculations
- Board generation
- Word validation (including Qu tile handling)
- Word finding algorithms
- Path finding

## Version History

**v1.3.0** (2026.01.23)
- Major refactor: Game state now managed by `GameState` class
- Added `requirements.txt` for dependency management
- Added comprehensive unit test suite (34 tests)
- Improved dictionary loading with better error handling
  - Handles encoding errors with automatic fallback
  - Validates dictionary is not empty
  - Handles permission errors gracefully
- Added serialization methods (`to_dict`/`from_dict`) for future save/load feature
- Code organization improvements with constants moved to top of file

**v1.2.5** (2026.01.19)
- Added 20 pixel navy blue rounded rectangle border around the grid
- Enhanced visual style with double-bordered rounded corners on letter tiles
- Fixed word validation for words with "Qu" tile in any position (not just at start)
- "Qu" tile now displays as "Qu" (mixed case) on the grid face

**v1.2.3** (2026.01.18)
- Fixed Qu scoring calculation
- Fixed division by zero in scrollbar rendering

## Author

no1453@gmail.com

## License

Feel free to use and modify this code for personal or educational purposes.
