"""Game review and retrospective analysis."""
import chess
from typing import List, Optional, Tuple
from dataclasses import dataclass
from ai import ChessAI


@dataclass
class MoveAnalysis:
    """Analysis of a single move."""
    move_number: int
    move: chess.Move
    san: str
    evaluation: float
    best_move: Optional[chess.Move]
    best_move_san: Optional[str]
    evaluation_diff: float  # Difference from best move
    classification: str  # "best", "good", "inaccuracy", "mistake", "blunder"
    explanation: str


class GameReviewer:
    """Reviews completed games with analysis."""

    def __init__(self, ai: ChessAI = None):
        self.ai = ai if ai else ChessAI()
        self.move_analyses: List[MoveAnalysis] = []
        self.positions: List[str] = []
        self.current_index: int = 0

    def analyze_game(self, moves: List[chess.Move]) -> List[MoveAnalysis]:
        """Analyze a complete game."""
        self.move_analyses = []
        self.positions = []
        board = chess.Board()
        self.positions.append(board.fen())

        for i, move in enumerate(moves):
            # Get evaluation before the move
            eval_before = self.ai._evaluate(board)

            # Find best move
            best_move = self.ai._minimax_root(board, depth=3)
            best_eval = eval_before

            if best_move:
                board.push(best_move)
                best_eval = -self.ai._evaluate(board)
                board.pop()

            # Make the actual move
            san = board.san(move)
            board.push(move)
            actual_eval = -self.ai._evaluate(board)

            self.positions.append(board.fen())

            # Calculate evaluation difference
            # From the perspective of the side that moved
            if best_move:
                eval_diff = abs(best_eval - actual_eval)
            else:
                eval_diff = 0

            # Classify the move
            classification, explanation = self._classify_move(
                board, move, best_move, eval_diff, actual_eval, i % 2 == 0
            )

            best_san = None
            if best_move and best_move != move:
                temp_board = chess.Board(self.positions[-2])
                best_san = temp_board.san(best_move)

            analysis = MoveAnalysis(
                move_number=(i // 2) + 1,
                move=move,
                san=san,
                evaluation=actual_eval,
                best_move=best_move if best_move != move else None,
                best_move_san=best_san,
                evaluation_diff=eval_diff,
                classification=classification,
                explanation=explanation
            )
            self.move_analyses.append(analysis)

        self.current_index = 0
        return self.move_analyses

    def _classify_move(self, board: chess.Board, move: chess.Move,
                       best_move: Optional[chess.Move], eval_diff: float,
                       evaluation: float, is_white: bool) -> Tuple[str, str]:
        """Classify a move and generate explanation."""
        # Check for checkmate
        if board.is_checkmate():
            return "best", "Checkmate!"

        # If it's the best move
        if best_move == move or eval_diff < 20:
            return "best", "Best move in the position."

        # Classification thresholds (in centipawns)
        if eval_diff < 50:
            classification = "good"
            explanation = "A good move, close to the best."
        elif eval_diff < 100:
            classification = "inaccuracy"
            explanation = "Slight inaccuracy - there was a better option."
        elif eval_diff < 300:
            classification = "mistake"
            explanation = "A mistake - this move loses some advantage."
        else:
            classification = "blunder"
            explanation = "A serious mistake - significant material or positional loss."

        return classification, explanation

    def get_game_summary(self) -> dict:
        """Get a summary of the game analysis."""
        if not self.move_analyses:
            return {}

        white_mistakes = sum(1 for a in self.move_analyses[::2]
                            if a.classification in ['mistake', 'blunder'])
        black_mistakes = sum(1 for a in self.move_analyses[1::2]
                            if a.classification in ['mistake', 'blunder'])

        white_inaccuracies = sum(1 for a in self.move_analyses[::2]
                                 if a.classification == 'inaccuracy')
        black_inaccuracies = sum(1 for a in self.move_analyses[1::2]
                                 if a.classification == 'inaccuracy')

        return {
            'total_moves': len(self.move_analyses),
            'white_mistakes': white_mistakes,
            'black_mistakes': black_mistakes,
            'white_inaccuracies': white_inaccuracies,
            'black_inaccuracies': black_inaccuracies,
            'critical_moments': self._find_critical_moments()
        }

    def _find_critical_moments(self) -> List[int]:
        """Find move indices where the game turned."""
        critical = []
        for i, analysis in enumerate(self.move_analyses):
            if analysis.classification in ['mistake', 'blunder']:
                critical.append(i)
        return critical[:5]  # Top 5 critical moments

    def go_to_move(self, index: int) -> Optional[str]:
        """Go to a specific move in the review."""
        if 0 <= index < len(self.positions):
            self.current_index = index
            return self.positions[index]
        return None

    def next_move(self) -> Optional[Tuple[str, MoveAnalysis]]:
        """Go to next move and return position + analysis."""
        if self.current_index < len(self.positions) - 1:
            self.current_index += 1
            analysis = self.move_analyses[self.current_index - 1] if self.current_index > 0 else None
            return self.positions[self.current_index], analysis
        return None

    def prev_move(self) -> Optional[str]:
        """Go to previous move."""
        if self.current_index > 0:
            self.current_index -= 1
            return self.positions[self.current_index]
        return None

    def first_move(self) -> str:
        """Go to starting position."""
        self.current_index = 0
        return self.positions[0]

    def last_move(self) -> str:
        """Go to final position."""
        self.current_index = len(self.positions) - 1
        return self.positions[self.current_index]

    def get_current_analysis(self) -> Optional[MoveAnalysis]:
        """Get analysis for current position."""
        if 0 < self.current_index <= len(self.move_analyses):
            return self.move_analyses[self.current_index - 1]
        return None

    def get_learning_points(self) -> List[str]:
        """Generate learning points from the game."""
        points = []

        summary = self.get_game_summary()

        # Check for common issues
        blunders = [a for a in self.move_analyses if a.classification == 'blunder']
        mistakes = [a for a in self.move_analyses if a.classification == 'mistake']

        if len(blunders) > 0:
            points.append(f"You had {len(blunders)} serious blunder(s). Take more time to check for threats!")

        if len(mistakes) > 2:
            points.append("Several mistakes occurred. Consider checking if your pieces are safe before moving.")

        # Opening phase analysis
        opening_moves = self.move_analyses[:10]
        opening_inaccuracies = sum(1 for a in opening_moves if a.classification != 'best')
        if opening_inaccuracies > 3:
            points.append("Opening could be improved. Study common opening principles.")

        if not points:
            points.append("Good game! Keep practicing to improve further.")

        return points
