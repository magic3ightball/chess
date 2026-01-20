"""AI opponent with Stockfish integration and fallback minimax."""
import chess
import chess.engine
import random
import shutil
from typing import Optional, Tuple
from enum import Enum


class Difficulty(Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3
    STOCKFISH = 4  # Full strength Stockfish


# Piece values for evaluation (used in fallback minimax)
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}


class ChessAI:
    """AI opponent for chess with Stockfish support."""

    def __init__(self, difficulty: Difficulty = Difficulty.MEDIUM):
        self.difficulty = difficulty
        self.positions_evaluated = 0
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.stockfish_path = self._find_stockfish()
        self._init_engine()

    def _find_stockfish(self) -> Optional[str]:
        """Find Stockfish executable."""
        # Check common locations
        path = shutil.which("stockfish")
        if path:
            return path

        # Try common macOS Homebrew paths
        for p in ["/opt/homebrew/bin/stockfish", "/usr/local/bin/stockfish"]:
            try:
                import os
                if os.path.exists(p):
                    return p
            except:
                pass
        return None

    def _init_engine(self):
        """Initialize Stockfish engine."""
        if self.stockfish_path:
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
                print(f"Stockfish loaded from {self.stockfish_path}")
            except Exception as e:
                print(f"Failed to load Stockfish: {e}")
                self.engine = None

    def __del__(self):
        """Clean up engine on destruction."""
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass

    def set_difficulty(self, difficulty: Difficulty):
        """Set the AI difficulty level."""
        self.difficulty = difficulty

    def has_stockfish(self) -> bool:
        """Check if Stockfish is available."""
        return self.engine is not None

    def get_best_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Get the best move for the current position."""
        self.positions_evaluated = 0

        # Use Stockfish if available and difficulty calls for it
        if self.engine and self.difficulty in [Difficulty.HARD, Difficulty.STOCKFISH]:
            return self._get_stockfish_move(board)
        elif self.engine and self.difficulty == Difficulty.MEDIUM:
            return self._get_stockfish_move(board, skill_level=5, time_limit=0.1)
        elif self.difficulty == Difficulty.EASY:
            return self._get_easy_move(board)
        else:
            # Fallback to minimax
            return self._get_minimax_move(board)

    def _get_stockfish_move(self, board: chess.Board, skill_level: int = 20,
                           time_limit: float = 0.5) -> Optional[chess.Move]:
        """Get move from Stockfish engine."""
        if not self.engine:
            return self._get_minimax_move(board)

        try:
            # Configure skill level (0-20, 20 is strongest)
            if self.difficulty == Difficulty.STOCKFISH:
                skill_level = 20
                time_limit = 1.0
            elif self.difficulty == Difficulty.HARD:
                skill_level = 15
                time_limit = 0.5
            elif self.difficulty == Difficulty.MEDIUM:
                skill_level = 5
                time_limit = 0.1

            self.engine.configure({"Skill Level": skill_level})

            result = self.engine.play(board, chess.engine.Limit(time=time_limit))
            return result.move
        except Exception as e:
            print(f"Stockfish error: {e}")
            return self._get_minimax_move(board)

    def _get_easy_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Easy: Mix of random and capture moves."""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        # 30% chance of making a capture if available
        captures = [m for m in legal_moves if board.is_capture(m)]
        if captures and random.random() < 0.3:
            return random.choice(captures)

        return random.choice(legal_moves)

    def _get_minimax_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Fallback minimax when Stockfish unavailable."""
        return self._minimax_root(board, depth=3)

    def _minimax_root(self, board: chess.Board, depth: int) -> Optional[chess.Move]:
        """Find best move using minimax with alpha-beta pruning."""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        best_move = None
        best_value = float('-inf') if board.turn else float('inf')

        legal_moves.sort(key=lambda m: board.is_capture(m), reverse=True)

        for move in legal_moves:
            board.push(move)
            value = self._minimax(board, depth - 1, float('-inf'), float('inf'), not board.turn)
            board.pop()

            if board.turn:
                if value > best_value:
                    best_value = value
                    best_move = move
            else:
                if value < best_value:
                    best_value = value
                    best_move = move

        return best_move

    def _minimax(self, board: chess.Board, depth: int, alpha: float, beta: float,
                 maximizing: bool) -> float:
        """Minimax algorithm with alpha-beta pruning."""
        self.positions_evaluated += 1

        if depth == 0 or board.is_game_over():
            return self._evaluate(board)

        legal_moves = list(board.legal_moves)

        if maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                board.push(move)
                eval_score = self._minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board.push(move)
                eval_score = self._minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def _evaluate(self, board: chess.Board) -> float:
        """Evaluate the board position."""
        if board.is_checkmate():
            return float('-inf') if board.turn else float('inf')
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = PIECE_VALUES[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value

        return score

    def analyze_position(self, board: chess.Board, time_limit: float = 0.5) -> dict:
        """Analyze position with Stockfish."""
        if not self.engine:
            return {"error": "Stockfish not available"}

        try:
            info = self.engine.analyse(board, chess.engine.Limit(time=time_limit))

            score = info.get("score")
            if score:
                if score.is_mate():
                    eval_str = f"Mate in {score.white().mate()}"
                else:
                    cp = score.white().score()
                    eval_str = f"{cp/100:+.2f}" if cp else "0.00"
            else:
                eval_str = "?"

            return {
                "evaluation": eval_str,
                "best_move": info.get("pv", [None])[0],
                "depth": info.get("depth", 0)
            }
        except Exception as e:
            return {"error": str(e)}

    def get_hint(self, board: chess.Board) -> Tuple[Optional[chess.Move], str]:
        """Get a hint for the current position."""
        if self.engine:
            try:
                info = self.engine.analyse(board, chess.engine.Limit(time=0.5))
                best_move = info.get("pv", [None])[0]
                if best_move:
                    explanation = self._explain_move(board, best_move)

                    # Add evaluation
                    score = info.get("score")
                    if score:
                        if score.is_mate():
                            explanation += f" (Mate in {abs(score.white().mate())})"
                        else:
                            cp = score.white().score()
                            if cp:
                                explanation += f" (Eval: {cp/100:+.2f})"

                    return best_move, explanation
            except:
                pass

        # Fallback
        best_move = self._minimax_root(board, depth=3)
        if best_move:
            explanation = self._explain_move(board, best_move)
            return best_move, explanation
        return None, "No moves available"

    def _explain_move(self, board: chess.Board, move: chess.Move) -> str:
        """Generate a simple explanation for a move."""
        explanations = []

        if board.is_capture(move):
            captured = board.piece_at(move.to_square)
            if captured:
                explanations.append(f"Captures {chess.piece_name(captured.piece_type)}")

        board.push(move)
        if board.is_check():
            if board.is_checkmate():
                explanations.append("Checkmate!")
            else:
                explanations.append("Check")
        board.pop()

        if board.is_castling(move):
            explanations.append("Castles for king safety")

        if move.promotion:
            explanations.append(f"Promotes to {chess.piece_name(move.promotion)}")

        central_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        if move.to_square in central_squares:
            explanations.append("Controls the center")

        if not explanations:
            explanations.append("Develops piece")

        return "; ".join(explanations)
