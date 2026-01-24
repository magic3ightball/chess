# Chess Learner

A chess learning application built with Pygame that helps you improve your chess skills through various training modes.

## Features

- **Play vs Computer** - Play against AI with 4 difficulty levels (Easy, Medium, Hard, Stockfish Max)
- **Puzzles** - Solve tactical puzzles with progress tracking
- **Opening Trainer** - Practice standard chess openings
- **Endgame Trainer** - Master essential endgame positions
- **Game Review** - Analyze your games with move quality feedback

### Additional Features

- Position evaluation bar with win probability
- Move quality indicators (best, excellent, good, inaccuracy, mistake, blunder)
- Hint system
- Sound effects
- Board flip
- Undo moves
- Game pause/resume

## Requirements

- Python 3.9+
- Pygame
- python-chess
- Stockfish (optional, for stronger AI and analysis)

## Installation

```bash
pip install pygame chess
```

For full AI strength, install Stockfish:
```bash
# macOS
brew install stockfish

# Ubuntu/Debian
sudo apt install stockfish
```

## Usage

```bash
python main.py
```

Or double-click `ChessLearner.command` on macOS.

## License

MIT
