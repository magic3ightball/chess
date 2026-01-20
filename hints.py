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

    def explain_move_quality(self, board: chess.Board, played_move: chess.Move) -> Tuple[str, str]:
        """Analyze move quality. Returns (badge_type, explanation)."""
        return self._analyze_move_quality(board, played_move)

    def _analyze_move_quality(self, board: chess.Board, played_move: chess.Move) -> Tuple[str, str]:
        """Analyze move quality and explain why it's good or bad.
        Returns (badge_type, explanation) where badge_type is one of:
        'best', 'excellent', 'good', 'inaccuracy', 'mistake', 'blunder'
        """
        if not self.ai.engine:
            return ("good", self.explain_move(board, played_move))

        try:
            # Get evaluation before move
            info_before = self.ai.engine.analyse(board, chess.engine.Limit(time=0.2))
            best_move = info_before.get("pv", [None])[0]
            score_before = info_before.get("score")

            # Get evaluation after played move
            board.push(played_move)
            info_after = self.ai.engine.analyse(board, chess.engine.Limit(time=0.1))
            score_after = info_after.get("score")
            board.pop()

            # Calculate centipawn loss
            if score_before and score_after:
                cp_before = self._get_cp_score(score_before, board.turn)
                cp_after = self._get_cp_score(score_after, board.turn)
                cp_loss = cp_before - cp_after if cp_before and cp_after else 0

                # Classify move quality
                quality, badge_type = self._classify_move(cp_loss, played_move, best_move)

                # Build explanation
                explanation = quality

                # Add specific reason
                reason = self._get_move_reason(board, played_move, best_move, cp_loss)
                if reason:
                    explanation += f" - {reason}"

                # Suggest better move if significant loss
                if cp_loss > 50 and best_move and best_move != played_move:
                    try:
                        better_san = board.san(best_move)
                        explanation += f" (Better: {better_san})"
                    except:
                        pass

                return (badge_type, explanation)

        except Exception as e:
            pass

        # Fallback to basic explanation
        return ("good", self.explain_move(board, played_move))

    def _get_cp_score(self, score, turn: bool) -> Optional[int]:
        """Convert score to centipawns from current player's perspective."""
        if score.is_mate():
            mate_in = score.white().mate()
            if mate_in:
                # Large positive/negative for mate
                return 10000 if (mate_in > 0) == turn else -10000
            return 0
        cp = score.white().score()
        if cp is not None:
            return cp if turn else -cp
        return None

    def _classify_move(self, cp_loss: int, played: chess.Move, best: chess.Move) -> Tuple[str, str]:
        """Classify move quality based on centipawn loss.
        Returns (quality_text, badge_type)."""
        if best and played == best:
            return "Best move!", "best"
        elif cp_loss <= 10:
            return "Excellent", "excellent"
        elif cp_loss <= 30:
            return "Good move", "good"
        elif cp_loss <= 80:
            return "Inaccuracy", "inaccuracy"
        elif cp_loss <= 200:
            return "Mistake", "mistake"
        else:
            return "Blunder!", "blunder"

    def _get_move_reason(self, board: chess.Board, played: chess.Move, best: chess.Move, cp_loss: int) -> str:
        """Get a human-readable reason for move quality."""
        reasons = []

        piece = board.piece_at(played.from_square)
        if not piece:
            return ""

        # Check what the played move does
        is_capture = board.is_capture(played)
        is_castle = board.is_castling(played)

        # Make the move temporarily to analyze
        board.push(played)
        gives_check = board.is_check()
        is_checkmate = board.is_checkmate()
        board.pop()

        if is_checkmate:
            return "Checkmate!"

        if gives_check:
            reasons.append("Gives check")

        if is_castle:
            reasons.append("King safety improved")

        if is_capture:
            captured = board.piece_at(played.to_square)
            if captured:
                # Check if it's a good capture
                piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                               chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
                gain = piece_values.get(captured.piece_type, 0) - piece_values.get(piece.piece_type, 0)
                if gain > 0:
                    reasons.append("Wins material")
                elif gain < 0 and cp_loss > 50:
                    reasons.append("Loses material")

        # Check for tactics if move was bad
        if cp_loss > 50 and best:
            tactic = self._detect_tactic(board, best)
            if tactic:
                reasons.append(f"Missed {tactic}")

        # Development in opening
        if len(board.move_stack) < 12:
            if piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                if not is_capture:
                    reasons.append("Develops piece")
            # Check center control
            if piece.piece_type == chess.PAWN:
                if played.to_square in [chess.E4, chess.D4, chess.E5, chess.D5]:
                    reasons.append("Controls center")

        # Hanging piece detection
        board.push(played)
        if self._is_piece_hanging(board, played.to_square):
            reasons.append("Piece may be vulnerable")
        board.pop()

        return "; ".join(reasons[:2]) if reasons else ""

    def _detect_tactic(self, board: chess.Board, move: chess.Move) -> Optional[str]:
        """Detect if a move involves a tactic."""
        board.push(move)

        # Check for fork
        piece = board.piece_at(move.to_square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.QUEEN, chess.PAWN]:
            attacked_valuable = 0
            for sq in chess.SQUARES:
                target = board.piece_at(sq)
                if target and target.color != piece.color:
                    if board.is_attacked_by(piece.color, sq):
                        if target.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                            attacked_valuable += 1
            if attacked_valuable >= 2:
                board.pop()
                return "fork"

        # Check for discovered attack
        if board.is_check():
            if piece and board.piece_at(move.to_square) != board.king(not piece.color):
                board.pop()
                return "discovered check"

        board.pop()

        # Check for pin
        for sq in chess.SQUARES:
            target = board.piece_at(sq)
            if target and target.color != board.turn:
                if self._is_pinned_after_move(board, move, sq):
                    return "pin"

        return None

    def _is_pinned_after_move(self, board: chess.Board, move: chess.Move, square: int) -> bool:
        """Check if a piece becomes pinned after a move."""
        board.push(move)
        is_pinned = board.is_pinned(not board.turn, square)
        board.pop()
        return is_pinned

    def _is_piece_hanging(self, board: chess.Board, square: int) -> bool:
        """Check if a piece on a square is hanging (attacked but not defended)."""
        piece = board.piece_at(square)
        if not piece:
            return False

        attackers = len(board.attackers(not piece.color, square))
        defenders = len(board.attackers(piece.color, square))

        return attackers > defenders
