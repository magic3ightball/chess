"""Endgame trainer for learning basic checkmate patterns."""
import chess
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Endgame:
    """Represents an endgame lesson."""
    name: str
    description: str
    fen: str  # Starting position
    goal: str  # What the player should achieve
    hints: List[str]  # Step-by-step hints
    key_squares: List[str]  # Important squares to highlight


class EndgameTrainer:
    """Teaches basic endgame techniques."""

    def __init__(self):
        self.endgames = self._create_endgames()
        self.current_endgame: Optional[Endgame] = None
        self.practice_board: Optional[chess.Board] = None
        self.hint_index = 0
        self.moves_made = 0

    def _create_endgames(self) -> List[Endgame]:
        """Create the endgame lesson database."""
        return [
            # King + Queen vs King
            Endgame(
                name="Queen Checkmate",
                description="Learn to checkmate with King and Queen",
                fen="8/8/8/4k3/8/8/8/4K2Q w - - 0 1",
                goal="Checkmate the black king",
                hints=[
                    "Use your Queen to restrict the enemy King",
                    "Push the enemy King to the edge of the board",
                    "Bring your King closer to help",
                    "Be careful not to stalemate!",
                    "Deliver checkmate on the edge"
                ],
                key_squares=["a1", "a8", "h1", "h8"]  # Corner squares
            ),

            # King + Rook vs King
            Endgame(
                name="Rook Checkmate",
                description="Learn to checkmate with King and Rook",
                fen="8/8/8/4k3/8/8/8/R3K3 w Q - 0 1",
                goal="Checkmate the black king",
                hints=[
                    "Cut off the enemy King with your Rook",
                    "Use your King to push the enemy King back",
                    "Keep your Rook far from the enemy King",
                    "Move your King in a 'staircase' pattern",
                    "Checkmate happens on the edge of the board"
                ],
                key_squares=["a8", "b8", "c8", "d8", "e8", "f8", "g8", "h8"]
            ),

            # King + 2 Bishops vs King
            Endgame(
                name="Two Bishops Checkmate",
                description="Learn to checkmate with two Bishops",
                fen="8/8/8/4k3/8/8/8/2B1KB2 w - - 0 1",
                goal="Checkmate the black king",
                hints=[
                    "Bishops work together on adjacent diagonals",
                    "Create a 'barrier' with your Bishops",
                    "Push the enemy King to a corner",
                    "Your King must help in the final attack",
                    "Checkmate occurs in the corner"
                ],
                key_squares=["a1", "a8", "h1", "h8"]
            ),

            # King + Pawn vs King (winning)
            Endgame(
                name="Pawn Endgame (Win)",
                description="Learn to promote a pawn and win",
                fen="8/4P3/8/4K3/8/8/4k3/8 w - - 0 1",
                goal="Promote the pawn to a Queen",
                hints=[
                    "Keep your King in front of the pawn",
                    "Use 'opposition' - Kings facing with one square between",
                    "Advance the pawn when the enemy King moves aside",
                    "Protect the pawn's promotion square",
                    "Once promoted, it's a Queen checkmate"
                ],
                key_squares=["e8", "d8", "f8"]
            ),

            # Opposition concept
            Endgame(
                name="The Opposition",
                description="Learn the key concept of King opposition",
                fen="8/8/8/8/3k4/8/3P4/3K4 w - - 0 1",
                goal="Use opposition to promote the pawn",
                hints=[
                    "Opposition: Kings face each other, one square apart",
                    "The player NOT to move has the opposition",
                    "Having opposition lets you push the enemy King aside",
                    "Advance your King before your pawn when possible",
                    "d4 is key - get your King there!"
                ],
                key_squares=["d3", "d4", "d5"]
            ),

            # Lucena Position
            Endgame(
                name="Lucena Position",
                description="The most important Rook endgame win",
                fen="1K1k4/1P6/8/8/8/8/1R6/8 w - - 0 1",
                goal="Promote the pawn using the 'bridge' technique",
                hints=[
                    "Your King is stuck - the enemy Rook will check",
                    "Build a 'bridge' with your Rook",
                    "Move your Rook to the 4th rank",
                    "After a check, block with your Rook",
                    "Then promote the pawn safely"
                ],
                key_squares=["b4", "c4", "d4"]
            ),

            # Philidor Position
            Endgame(
                name="Philidor Defense",
                description="The most important Rook endgame draw",
                fen="8/3k4/8/3KP3/8/8/8/3r4 b - - 0 1",
                goal="Hold the draw as Black",
                hints=[
                    "Keep your Rook on the 3rd rank (from your side)",
                    "This stops the enemy King from advancing",
                    "When the pawn advances, go to the back rank",
                    "Check from behind - the King can't hide",
                    "This technique saves many 'lost' positions"
                ],
                key_squares=["d1", "d2", "d3", "d6"]
            ),

            # Back Rank Mate Pattern
            Endgame(
                name="Back Rank Checkmate",
                description="Exploit a trapped King on the back rank",
                fen="6k1/5ppp/8/8/8/8/8/R3K3 w Q - 0 1",
                goal="Checkmate in one move",
                hints=[
                    "The King is trapped by its own pawns",
                    "A Rook or Queen on the back rank is deadly",
                    "This is why you should make 'luft' (escape square)",
                    "Ra8 is checkmate!"
                ],
                key_squares=["a8", "g8"]
            ),
        ]

    def get_all_endgames(self) -> List[Endgame]:
        """Get all available endgame lessons."""
        return self.endgames

    def start_practice(self, endgame: Endgame) -> chess.Board:
        """Start practicing an endgame."""
        self.current_endgame = endgame
        self.practice_board = chess.Board(endgame.fen)
        self.hint_index = 0
        self.moves_made = 0
        return self.practice_board

    def get_hint(self) -> Optional[str]:
        """Get the next hint for the current endgame."""
        if not self.current_endgame:
            return None

        if self.hint_index < len(self.current_endgame.hints):
            hint = self.current_endgame.hints[self.hint_index]
            self.hint_index += 1
            return hint
        return "No more hints. Keep trying!"

    def make_move(self, move: chess.Move) -> Tuple[bool, str]:
        """Make a move and check progress."""
        if not self.practice_board or not self.current_endgame:
            return False, "No endgame in progress"

        if move not in self.practice_board.legal_moves:
            return False, "Illegal move"

        self.practice_board.push(move)
        self.moves_made += 1

        # Check for success conditions
        if self.practice_board.is_checkmate():
            return True, f"Checkmate! Completed in {self.moves_made} moves!"

        if self.practice_board.is_stalemate():
            return False, "Stalemate! Be careful not to trap the King."

        # Check for pawn promotion
        if move.promotion:
            return True, "Pawn promoted! Now finish the checkmate."

        # Make a simple AI response (move the King to avoid mate)
        self._make_defensive_move()

        if self.practice_board.is_checkmate():
            return True, f"Checkmate! Excellent! ({self.moves_made} moves)"

        return True, "Good move! Keep going."

    def _make_defensive_move(self):
        """Make a simple defensive move for the opponent."""
        if not self.practice_board or self.practice_board.is_game_over():
            return

        # Try to find a move that avoids immediate checkmate
        best_move = None
        for move in self.practice_board.legal_moves:
            self.practice_board.push(move)
            is_checkmate = self.practice_board.is_checkmate()
            self.practice_board.pop()

            if not is_checkmate:
                best_move = move
                # Prefer King moves
                if self.practice_board.piece_at(move.from_square).piece_type == chess.KING:
                    break

        if best_move:
            self.practice_board.push(best_move)
        elif list(self.practice_board.legal_moves):
            # If all moves lead to mate, just pick one
            self.practice_board.push(list(self.practice_board.legal_moves)[0])

    def get_progress_message(self) -> str:
        """Get a message about current progress."""
        if not self.current_endgame or not self.practice_board:
            return ""

        if self.practice_board.is_checkmate():
            return "Checkmate!"
        if self.practice_board.is_stalemate():
            return "Stalemate - try again"
        if self.practice_board.is_insufficient_material():
            return "Draw - insufficient material"

        return f"Moves: {self.moves_made} | {self.current_endgame.goal}"
