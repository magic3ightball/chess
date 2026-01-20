"""Opening trainer for learning chess openings."""
import chess
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Opening:
    """A chess opening."""
    name: str
    eco: str  # ECO code
    moves: List[str]  # SAN notation
    description: str
    key_ideas: List[str]


# Popular openings for beginners
OPENINGS = [
    # e4 openings
    Opening(
        "Italian Game",
        "C50",
        ["e4", "e5", "Nf3", "Nc6", "Bc4"],
        "One of the oldest openings, aiming for quick development and central control.",
        [
            "Control the center with e4",
            "Develop knights before bishops",
            "Put bishop on active diagonal targeting f7",
            "Castle kingside for safety",
            "d3 and c3 to support center"
        ]
    ),
    Opening(
        "Italian Game - Giuoco Piano",
        "C53",
        ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5"],
        "The 'Quiet Game' - a solid response by Black.",
        [
            "Both sides develop symmetrically",
            "Fight for center control",
            "c3 and d4 push is a key plan for White",
            "Black should challenge the center"
        ]
    ),
    Opening(
        "Ruy Lopez",
        "C60",
        ["e4", "e5", "Nf3", "Nc6", "Bb5"],
        "The Spanish Game - one of the most popular openings at all levels.",
        [
            "Bishop pressures the knight defending e5",
            "White aims for slow, strategic play",
            "a6 is the main response, asking the bishop's intentions",
            "Castling and d3 are key moves"
        ]
    ),
    Opening(
        "Scotch Game",
        "C45",
        ["e4", "e5", "Nf3", "Nc6", "d4"],
        "An aggressive opening that immediately opens the center.",
        [
            "White immediately strikes in the center",
            "exd4 is the main response",
            "White gets open lines and active pieces",
            "Good for players who like open positions"
        ]
    ),
    Opening(
        "King's Gambit",
        "C30",
        ["e4", "e5", "f4"],
        "A romantic, aggressive opening sacrificing a pawn for attack.",
        [
            "White sacrifices the f-pawn for central control",
            "Leads to sharp, tactical positions",
            "Not seen much at top level but great for learning attacks",
            "exf4 accepts, d5 or Bc5 decline"
        ]
    ),

    # d4 openings
    Opening(
        "Queen's Gambit",
        "D06",
        ["d4", "d5", "c4"],
        "A classical opening offering a pawn sacrifice to control the center.",
        [
            "White offers c4 pawn to deflect d5",
            "If dxc4, White recaptures later with central control",
            "e6 defends solidly (Queen's Gambit Declined)",
            "c6 also defends (Slav Defense)"
        ]
    ),
    Opening(
        "London System",
        "D02",
        ["d4", "d5", "Nf3", "Nf6", "Bf4"],
        "A solid, easy-to-learn system for White.",
        [
            "Bishop goes to f4 early, before e3",
            "Very consistent setup regardless of Black's response",
            "e3, c3, Bd3, Nbd2, O-O is the typical setup",
            "Solid and hard to crack"
        ]
    ),
    Opening(
        "King's Indian Defense",
        "E60",
        ["d4", "Nf6", "c4", "g6"],
        "A hypermodern defense allowing White the center before striking back.",
        [
            "Black lets White build a big center",
            "Fianchetto bishop on g7 attacks the center",
            "d6, O-O, e5 is the typical plan",
            "Sharp and fighting"
        ]
    ),

    # Other popular
    Opening(
        "Sicilian Defense",
        "B20",
        ["e4", "c5"],
        "The most popular response to 1.e4, leading to complex positions.",
        [
            "Black fights for the center asymmetrically",
            "Leads to unbalanced, fighting positions",
            "Many variations: Najdorf, Dragon, Scheveningen",
            "Good for players who want to play for a win as Black"
        ]
    ),
    Opening(
        "French Defense",
        "C00",
        ["e4", "e6"],
        "A solid defense leading to strategic battles.",
        [
            "Black prepares d5 to challenge the center",
            "The light-squared bishop can be a problem",
            "Leads to closed positions",
            "Solid and hard to crack"
        ]
    ),
    Opening(
        "Caro-Kann Defense",
        "B10",
        ["e4", "c6"],
        "A solid defense preparing d5 without blocking the bishop.",
        [
            "Black prepares d5 while keeping bishop active",
            "Very solid and reliable",
            "Less tactical than Sicilian but solid",
            "Good for beginners learning defense"
        ]
    ),
]


class OpeningTrainer:
    """Interactive opening trainer."""

    def __init__(self):
        self.openings = OPENINGS
        self.current_opening: Optional[Opening] = None
        self.current_move_index: int = 0
        self.practice_board: Optional[chess.Board] = None
        self.user_color: bool = True  # True = White

    def get_all_openings(self) -> List[Opening]:
        """Get all available openings."""
        return self.openings

    def get_openings_for_white(self) -> List[Opening]:
        """Get openings suitable for White."""
        return [o for o in self.openings if o.moves[0][0].isupper() or o.moves[0][0] in 'abcdefgh']

    def get_openings_for_black(self) -> List[Opening]:
        """Get openings responding to e4 or d4."""
        return [o for o in self.openings if o.moves[0] in ['e5', 'c5', 'e6', 'c6', 'd5', 'Nf6', 'g6']]

    def start_practice(self, opening: Opening, play_as_white: bool = True) -> chess.Board:
        """Start practicing an opening."""
        self.current_opening = opening
        self.current_move_index = 0
        self.user_color = play_as_white
        self.practice_board = chess.Board()

        # If playing as Black, make White's first move
        if not play_as_white and self.current_move_index < len(opening.moves):
            move = self.practice_board.parse_san(opening.moves[self.current_move_index])
            self.practice_board.push(move)
            self.current_move_index += 1

        return self.practice_board

    def check_move(self, move: chess.Move) -> Tuple[bool, str]:
        """Check if the move matches the opening."""
        if not self.current_opening or not self.practice_board:
            return False, "No opening practice active"

        if self.current_move_index >= len(self.current_opening.moves):
            return True, "Opening complete! You can continue playing freely."

        expected_san = self.current_opening.moves[self.current_move_index]
        expected_move = self.practice_board.parse_san(expected_san)

        if move == expected_move:
            self.practice_board.push(move)
            self.current_move_index += 1

            # Make opponent's response
            if self.current_move_index < len(self.current_opening.moves):
                opponent_san = self.current_opening.moves[self.current_move_index]
                opponent_move = self.practice_board.parse_san(opponent_san)
                self.practice_board.push(opponent_move)
                self.current_move_index += 1

            # Check if opening is complete
            if self.current_move_index >= len(self.current_opening.moves):
                return True, f"Well done! You've completed the {self.current_opening.name}!"

            return True, "Correct! Keep going..."
        else:
            actual_san = self.practice_board.san(move)
            return False, f"The opening move is {expected_san}, not {actual_san}"

    def get_next_move_hint(self) -> Optional[str]:
        """Get the next expected move."""
        if not self.current_opening or self.current_move_index >= len(self.current_opening.moves):
            return None

        move_san = self.current_opening.moves[self.current_move_index]
        return f"Next move: {move_san}"

    def get_current_idea(self) -> Optional[str]:
        """Get the key idea for the current position."""
        if not self.current_opening:
            return None

        # Return relevant key idea based on move number
        idea_index = min(self.current_move_index // 2, len(self.current_opening.key_ideas) - 1)
        return self.current_opening.key_ideas[idea_index]

    def detect_opening(self, board: chess.Board) -> Optional[Opening]:
        """Detect which opening is being played."""
        move_sans = []
        temp_board = chess.Board()

        for move in board.move_stack[:10]:  # Check first 10 moves
            move_sans.append(temp_board.san(move))
            temp_board.push(move)

        # Find matching opening
        best_match = None
        best_match_len = 0

        for opening in self.openings:
            match_len = 0
            for i, expected_san in enumerate(opening.moves):
                if i < len(move_sans) and move_sans[i] == expected_san:
                    match_len += 1
                else:
                    break

            if match_len > best_match_len and match_len >= 2:
                best_match = opening
                best_match_len = match_len

        return best_match
