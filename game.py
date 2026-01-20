"""Game state management using python-chess."""
import chess
import chess.pgn
from typing import Optional, List, Tuple
from datetime import datetime
import io


class ChessGame:
    """Wrapper around python-chess for game state management."""

    def __init__(self):
        self.board = chess.Board()
        self.move_history: List[chess.Move] = []
        self.position_history: List[str] = [self.board.fen()]
        self.start_time = datetime.now()

    def reset(self):
        """Reset the game to starting position."""
        self.board.reset()
        self.move_history = []
        self.position_history = [self.board.fen()]
        self.start_time = datetime.now()

    def make_move(self, move: chess.Move) -> bool:
        """Make a move if it's legal."""
        if move in self.board.legal_moves:
            self.board.push(move)
            self.move_history.append(move)
            self.position_history.append(self.board.fen())
            return True
        return False

    def make_move_uci(self, uci: str) -> bool:
        """Make a move from UCI string (e.g., 'e2e4')."""
        try:
            move = chess.Move.from_uci(uci)
            return self.make_move(move)
        except ValueError:
            return False

    def make_move_san(self, san: str) -> bool:
        """Make a move from SAN notation (e.g., 'e4', 'Nf3')."""
        try:
            move = self.board.parse_san(san)
            return self.make_move(move)
        except ValueError:
            return False

    def undo_move(self) -> Optional[chess.Move]:
        """Undo the last move."""
        if self.move_history:
            move = self.board.pop()
            self.move_history.pop()
            self.position_history.pop()
            return move
        return None

    def get_legal_moves(self) -> List[chess.Move]:
        """Get all legal moves in current position."""
        return list(self.board.legal_moves)

    def get_legal_moves_for_square(self, square: int) -> List[chess.Move]:
        """Get legal moves for a piece on a specific square."""
        return [m for m in self.board.legal_moves if m.from_square == square]

    def get_piece_at(self, square: int) -> Optional[chess.Piece]:
        """Get the piece at a square."""
        return self.board.piece_at(square)

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.board.is_game_over()

    def get_game_result(self) -> Optional[str]:
        """Get the game result if game is over."""
        if self.board.is_checkmate():
            return "White wins!" if self.board.turn == chess.BLACK else "Black wins!"
        elif self.board.is_stalemate():
            return "Stalemate - Draw!"
        elif self.board.is_insufficient_material():
            return "Draw - Insufficient material"
        elif self.board.is_fifty_moves():
            return "Draw - Fifty move rule"
        elif self.board.is_repetition():
            return "Draw - Repetition"
        return None

    def is_check(self) -> bool:
        """Check if current player is in check."""
        return self.board.is_check()

    def get_turn(self) -> bool:
        """Get current turn (True = White, False = Black)."""
        return self.board.turn

    def get_move_san(self, move: chess.Move) -> str:
        """Get SAN notation for a move."""
        return self.board.san(move)

    def get_pgn(self) -> str:
        """Export game as PGN string."""
        game = chess.pgn.Game()
        game.headers["Event"] = "Chess Learner Game"
        game.headers["Date"] = self.start_time.strftime("%Y.%m.%d")

        node = game
        temp_board = chess.Board()
        for move in self.move_history:
            node = node.add_variation(move)
            temp_board.push(move)

        game.headers["Result"] = self.board.result()

        return str(game)

    def load_fen(self, fen: str) -> bool:
        """Load a position from FEN string."""
        try:
            self.board.set_fen(fen)
            self.move_history = []
            self.position_history = [fen]
            return True
        except ValueError:
            return False

    def get_captured_pieces(self) -> Tuple[List[chess.PieceType], List[chess.PieceType]]:
        """Get captured pieces for each side."""
        # Count pieces in starting position
        start_white = {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2,
                       chess.ROOK: 2, chess.QUEEN: 1, chess.KING: 1}
        start_black = dict(start_white)

        # Count current pieces
        current_white = {pt: 0 for pt in start_white}
        current_black = {pt: 0 for pt in start_black}

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE:
                    current_white[piece.piece_type] += 1
                else:
                    current_black[piece.piece_type] += 1

        # Calculate captured pieces (excluding king)
        white_captured = []  # Black pieces captured by white
        black_captured = []  # White pieces captured by black

        for pt in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            white_captured.extend([pt] * (start_black[pt] - current_black[pt]))
            black_captured.extend([pt] * (start_white[pt] - current_white[pt]))

        return white_captured, black_captured

    def go_to_position(self, index: int) -> bool:
        """Go to a specific position in history."""
        if 0 <= index < len(self.position_history):
            self.board.set_fen(self.position_history[index])
            return True
        return False
