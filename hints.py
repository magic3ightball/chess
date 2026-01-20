"""Move hints and suggestions for learning."""
import chess
from typing import List, Tuple, Optional
from ai import ChessAI


class HintSystem:
    """Provides hints and move suggestions."""

    def __init__(self, ai: ChessAI = None):
        self.ai = ai if ai else ChessAI()

    def get_legal_move_squares(self, board: chess.Board, from_square: int) -> List[int]:
        """Get all squares a piece can legally move to."""
        moves = [m for m in board.legal_moves if m.from_square == from_square]
        return [m.to_square for m in moves]

    def get_best_move_hint(self, board: chess.Board) -> Tuple[Optional[chess.Move], str]:
        """Get the best move and explanation."""
        return self.ai.get_hint(board)

    def analyze_position(self, board: chess.Board) -> dict:
        """Analyze current position and provide insights."""
        analysis = {
            'material_balance': self._calculate_material_balance(board),
            'threats': self._find_threats(board),
            'hanging_pieces': self._find_hanging_pieces(board),
            'checks_available': self._find_checks(board),
            'position_tips': self._get_position_tips(board)
        }
        return analysis

    def _calculate_material_balance(self, board: chess.Board) -> int:
        """Calculate material balance (positive = white advantage)."""
        values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                  chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

        balance = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = values[piece.piece_type]
                if piece.color == chess.WHITE:
                    balance += value
                else:
                    balance -= value
        return balance

    def _find_threats(self, board: chess.Board) -> List[str]:
        """Find threats in the position."""
        threats = []

        # Check if opponent can capture something valuable
        board_copy = board.copy()
        board_copy.turn = not board_copy.turn

        for move in board_copy.legal_moves:
            if board_copy.is_capture(move):
                captured = board_copy.piece_at(move.to_square)
                if captured and captured.piece_type in [chess.QUEEN, chess.ROOK]:
                    attacker = board_copy.piece_at(move.from_square)
                    threats.append(f"{chess.piece_name(attacker.piece_type).title()} threatens {chess.piece_name(captured.piece_type)}")

        return threats[:3]  # Limit to 3 most relevant

    def _find_hanging_pieces(self, board: chess.Board) -> List[str]:
        """Find undefended pieces."""
        hanging = []
        turn = board.turn

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == turn:
                # Check if piece is attacked
                if board.is_attacked_by(not turn, square):
                    # Check if piece is defended
                    defenders = len(board.attackers(turn, square))
                    attackers = len(board.attackers(not turn, square))
                    if attackers > defenders:
                        hanging.append(f"{chess.piece_name(piece.piece_type).title()} on {chess.square_name(square)} is hanging!")

        return hanging[:3]

    def _find_checks(self, board: chess.Board) -> List[chess.Move]:
        """Find moves that give check."""
        checks = []
        for move in board.legal_moves:
            board.push(move)
            if board.is_check():
                checks.append(move)
            board.pop()
        return checks

    def _get_position_tips(self, board: chess.Board) -> List[str]:
        """Get general tips for the position."""
        tips = []
        turn = "White" if board.turn else "Black"

        # Opening principles
        if len(board.move_stack) < 10:
            # Check center control
            central_pawns = 0
            for sq in [chess.E4, chess.D4, chess.E5, chess.D5]:
                piece = board.piece_at(sq)
                if piece and piece.piece_type == chess.PAWN:
                    central_pawns += 1

            if central_pawns < 2:
                tips.append("Consider controlling the center with pawns (e4, d4)")

            # Check piece development
            developed = 0
            back_rank = range(8) if board.turn else range(56, 64)
            for sq in back_rank:
                piece = board.piece_at(sq)
                if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                    developed += 1

            if developed > 2:
                tips.append("Develop your knights and bishops!")

            # Check castling
            if board.has_castling_rights(board.turn):
                tips.append("Consider castling to protect your king")

        # Check if in check
        if board.is_check():
            tips.append(f"{turn} is in check! Must respond to the check.")

        return tips

    def explain_move(self, board: chess.Board, move: chess.Move) -> str:
        """Explain what a move does."""
        explanations = []

        piece = board.piece_at(move.from_square)
        piece_name = chess.piece_name(piece.piece_type).title()

        # Basic move description
        from_sq = chess.square_name(move.from_square)
        to_sq = chess.square_name(move.to_square)

        # Capture
        if board.is_capture(move):
            captured = board.piece_at(move.to_square)
            if captured:
                explanations.append(f"{piece_name} captures {chess.piece_name(captured.piece_type)} on {to_sq}")
            else:
                explanations.append(f"{piece_name} captures en passant on {to_sq}")
        else:
            explanations.append(f"{piece_name} moves from {from_sq} to {to_sq}")

        # Special moves
        if board.is_castling(move):
            if chess.square_file(move.to_square) > chess.square_file(move.from_square):
                explanations.append("Kingside castle (short castle)")
            else:
                explanations.append("Queenside castle (long castle)")

        if move.promotion:
            explanations.append(f"Pawn promotes to {chess.piece_name(move.promotion)}")

        # Check
        board.push(move)
        if board.is_check():
            if board.is_checkmate():
                explanations.append("CHECKMATE!")
            else:
                explanations.append("Check!")
        board.pop()

        return " | ".join(explanations)
