"""Chess puzzles for tactical training."""
import chess
from typing import List, Optional, Tuple
from dataclasses import dataclass
import json
import os


@dataclass
class Puzzle:
    """A chess puzzle."""
    id: str
    name: str
    fen: str
    solution: List[str]  # Moves in UCI format
    theme: str
    difficulty: int  # 1-5
    description: str


# Built-in puzzles for beginners
BUILTIN_PUZZLES = [
    # Mate in 1 puzzles
    Puzzle("m1_01", "Back Rank Mate",
           "6k1/5ppp/8/8/8/8/8/R3K3 w Q - 0 1",
           ["a1a8"], "mate_in_1", 1,
           "White to play - Find the back rank checkmate!"),

    Puzzle("m1_02", "Queen Mate",
           "k7/8/1K6/8/8/8/8/Q7 w - - 0 1",
           ["a1a8"], "mate_in_1", 1,
           "White to play - Deliver checkmate with the queen!"),

    Puzzle("m1_03", "Rook Checkmate",
           "k7/8/K7/8/8/8/8/R7 w - - 0 1",
           ["a1a8"], "mate_in_1", 1,
           "White to play - Use the rook to checkmate!"),

    Puzzle("m1_04", "Bishop & Knight Help",
           "5rk1/5ppp/8/8/8/5B2/8/4K2R w K - 0 1",
           ["h1h8"], "mate_in_1", 1,
           "White to play - The bishop controls the escape square!"),

    Puzzle("m1_05", "Smothered Mate",
           "6rk/5Npp/8/8/8/8/8/4K3 w - - 0 1",
           ["f7h6"], "mate_in_1", 2,
           "White to play - Knight delivers smothered mate!"),

    # Mate in 2 puzzles
    Puzzle("m2_01", "Queen Sacrifice",
           "r1b1kb1r/pppp1ppp/2n2n2/4N2Q/2B1P3/8/PPPP1PPP/RNB1K2R w KQkq - 0 1",
           ["h5f7"], "mate_in_2", 2,
           "White to play - Famous 'Scholar's Mate' pattern. Can you find it?"),

    Puzzle("m2_02", "Back Rank Theme",
           "3r2k1/5pp1/7p/8/8/8/1Q3PPP/6K1 w - - 0 1",
           ["b2b8"], "mate_in_2", 2,
           "White to play - Exploit the weak back rank!"),

    # Fork puzzles
    Puzzle("fork_01", "Knight Fork",
           "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1",
           ["f3g5"], "fork", 2,
           "White to play - Find the knight fork!"),

    Puzzle("fork_02", "Queen Fork",
           "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1",
           ["f1b5"], "fork", 2,
           "White to play - Pin the knight to the king!"),

    # Pin puzzles
    Puzzle("pin_01", "Absolute Pin",
           "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1",
           ["c1g5"], "pin", 2,
           "White to play - Pin the knight to the queen!"),

    # Discovered attack
    Puzzle("disc_01", "Discovered Check",
           "r1bqkb1r/pppp1ppp/2n2n2/4N3/2B1P3/8/PPPP1PPP/RNBQK2R w KQkq - 0 1",
           ["e5f7"], "discovered_attack", 3,
           "White to play - Use a discovered attack!"),

    # Skewer
    Puzzle("skewer_01", "Rook Skewer",
           "8/8/8/8/8/1k6/8/1RK1r3 w - - 0 1",
           ["b1b3"], "skewer", 3,
           "White to play - Skewer the king and rook!"),

    # More advanced
    Puzzle("m2_03", "Anastasia's Mate",
           "5rk1/1b3ppp/8/2n1N3/8/8/1Q3PPP/6K1 w - - 0 1",
           ["e5f7", "f8f7", "b2g7"], "mate_in_2", 4,
           "White to play and mate in 2!"),

    Puzzle("tactic_01", "Winning Material",
           "r2qkb1r/ppp2ppp/2np1n2/4p3/2B1P1b1/3P1N2/PPP2PPP/RNBQ1RK1 w kq - 0 1",
           ["c4f7"], "winning_material", 3,
           "White to play - Win material with a tactic!"),
]


class PuzzleManager:
    """Manages chess puzzles."""

    def __init__(self, data_path: str = "data/puzzles.json"):
        self.puzzles: List[Puzzle] = list(BUILTIN_PUZZLES)
        self.current_puzzle: Optional[Puzzle] = None
        self.current_move_index: int = 0
        self.solved_puzzles: set = set()
        self.practice_board: Optional[chess.Board] = None
        self.data_path = data_path
        self._load_progress()

    def _load_progress(self):
        """Load solved puzzle progress."""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    self.solved_puzzles = set(data.get('solved', []))
        except (json.JSONDecodeError, IOError):
            pass

    def _save_progress(self):
        """Save solved puzzle progress."""
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, 'w') as f:
                json.dump({'solved': list(self.solved_puzzles)}, f)
        except IOError:
            pass

    def get_puzzles_by_theme(self, theme: str) -> List[Puzzle]:
        """Get puzzles by theme."""
        return [p for p in self.puzzles if p.theme == theme]

    def get_puzzles_by_difficulty(self, difficulty: int) -> List[Puzzle]:
        """Get puzzles by difficulty level."""
        return [p for p in self.puzzles if p.difficulty == difficulty]

    def get_unsolved_puzzles(self) -> List[Puzzle]:
        """Get unsolved puzzles."""
        return [p for p in self.puzzles if p.id not in self.solved_puzzles]

    def get_all_themes(self) -> List[str]:
        """Get all available themes."""
        return list(set(p.theme for p in self.puzzles))

    def start_puzzle(self, puzzle: Puzzle) -> chess.Board:
        """Start a puzzle and return the board."""
        self.current_puzzle = puzzle
        self.current_move_index = 0
        self.practice_board = chess.Board(puzzle.fen)
        return self.practice_board

    def check_move(self, board: chess.Board, move: chess.Move) -> Tuple[bool, str]:
        """Check if a move is correct for the current puzzle."""
        if not self.current_puzzle or not self.practice_board:
            return False, "No puzzle active"

        expected_uci = self.current_puzzle.solution[self.current_move_index]

        if move.uci() == expected_uci:
            self.current_move_index += 1
            self.practice_board.push(move)

            # Check if puzzle is complete
            if self.current_move_index >= len(self.current_puzzle.solution):
                self.solved_puzzles.add(self.current_puzzle.id)
                self._save_progress()
                return True, "Correct! Puzzle solved!"

            # Make opponent's response if there is one
            if self.current_move_index < len(self.current_puzzle.solution):
                opponent_move = chess.Move.from_uci(
                    self.current_puzzle.solution[self.current_move_index])
                self.practice_board.push(opponent_move)
                self.current_move_index += 1

                if self.current_move_index >= len(self.current_puzzle.solution):
                    self.solved_puzzles.add(self.current_puzzle.id)
                    self._save_progress()
                    return True, "Correct! Puzzle solved!"

                return True, "Correct! Find the next move..."

            return True, "Correct!"
        else:
            return False, "Not the best move. Try again!"

    def get_hint(self) -> Optional[str]:
        """Get a hint for the current puzzle."""
        if not self.current_puzzle or self.current_move_index >= len(self.current_puzzle.solution):
            return None

        move_uci = self.current_puzzle.solution[self.current_move_index]
        move = chess.Move.from_uci(move_uci)

        # Give piece type hint
        return f"Hint: Move your piece from {move_uci[:2]}"

    def get_progress(self) -> Tuple[int, int]:
        """Get puzzle progress (solved, total)."""
        return len(self.solved_puzzles), len(self.puzzles)
