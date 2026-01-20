#!/usr/bin/env python3
"""Chess Learner - A chess learning application."""
import pygame
import chess
import sys
import socket
from typing import Optional, List
from enum import Enum

# Single instance lock
LOCK_PORT = 47193  # Arbitrary port for single-instance check

def acquire_lock():
    """Try to acquire single-instance lock. Returns socket if successful, None if already running."""
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('127.0.0.1', LOCK_PORT))
        lock_socket.listen(1)
        return lock_socket
    except socket.error:
        return None

from game import ChessGame
from board import ChessBoard
from ai import ChessAI, Difficulty
from hints import HintSystem
from puzzles import PuzzleManager, Puzzle
from openings import OpeningTrainer, Opening
from review import GameReviewer
from endgames import EndgameTrainer, Endgame

# Window settings
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
BOARD_SIZE = 560
SQUARE_SIZE = BOARD_SIZE // 8
BOARD_X = 30
BOARD_Y = 70

# Colors
BG_COLOR = (35, 35, 40)
PANEL_COLOR = (50, 50, 55)
TEXT_COLOR = (220, 220, 220)
ACCENT_COLOR = (100, 149, 237)
SUCCESS_COLOR = (100, 200, 100)
ERROR_COLOR = (200, 100, 100)
BUTTON_COLOR = (70, 70, 80)
BUTTON_HOVER = (90, 90, 100)


class GameMode(Enum):
    MENU = 0
    PLAY_VS_AI = 1
    PUZZLE = 2
    OPENING = 3
    REVIEW = 4
    ENDGAME = 5


class Button:
    """Simple button class."""

    def __init__(self, x: int, y: int, width: int, height: int, text: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font):
        color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, ACCENT_COLOR, self.rect, 2, border_radius=5)

        text_surface = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def is_clicked(self, pos: tuple) -> bool:
        return self.rect.collidepoint(pos)

    def update_hover(self, pos: tuple):
        self.hovered = self.rect.collidepoint(pos)


class ChessLearner:
    """Main application class."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Chess Learner")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Fonts
        self.title_font = pygame.font.SysFont('arial', 32, bold=True)
        self.font = pygame.font.SysFont('arial', 18)
        self.small_font = pygame.font.SysFont('arial', 14)

        # Components
        self.game = ChessGame()
        self.board_view = ChessBoard(BOARD_X, BOARD_Y, SQUARE_SIZE)
        self.ai = ChessAI(Difficulty.MEDIUM)
        # Share AI instance to avoid multiple Stockfish engines
        self.hints = HintSystem(self.ai)
        self.puzzles = PuzzleManager()
        self.openings = OpeningTrainer()
        self.reviewer = GameReviewer(self.ai)
        self.endgames = EndgameTrainer()

        # State
        self.mode = GameMode.MENU
        self.selected_square: Optional[int] = None
        self.message = ""
        self.message_color = TEXT_COLOR
        self.player_color = chess.WHITE
        self.ai_thinking = False
        self.show_hints = True
        self.current_puzzle: Optional[Puzzle] = None
        self.current_opening: Optional[Opening] = None
        self.current_endgame: Optional[Endgame] = None
        self.game_over = False
        self.saved_game_moves: List[chess.Move] = []  # Store last game for review
        self.show_eval = False  # Toggle for showing win rate/evaluation
        self.current_eval = "0.00"  # Current position evaluation
        self.white_win_prob = 50  # Win probability percentage
        self.eval_reason = ""  # Explanation for the evaluation
        self.paused_game = None  # Store paused game state for resume

        # Buttons
        self.menu_buttons = [
            Button(WINDOW_WIDTH // 2 - 120, 160, 240, 45, "Play vs Computer"),
            Button(WINDOW_WIDTH // 2 - 120, 215, 240, 45, "Resume Game"),
            Button(WINDOW_WIDTH // 2 - 120, 270, 240, 45, "Puzzles"),
            Button(WINDOW_WIDTH // 2 - 120, 325, 240, 45, "Opening Trainer"),
            Button(WINDOW_WIDTH // 2 - 120, 380, 240, 45, "Endgame Trainer"),
            Button(WINDOW_WIDTH // 2 - 120, 435, 240, 45, "Review Last Game"),
            Button(WINDOW_WIDTH // 2 - 120, 510, 240, 40, "Quit"),
        ]

        self.game_buttons = [
            Button(BOARD_X + BOARD_SIZE + 30, 500, 100, 35, "Hint"),
            Button(BOARD_X + BOARD_SIZE + 140, 500, 100, 35, "Undo"),
            Button(BOARD_X + BOARD_SIZE + 30, 545, 100, 35, "New Game"),
            Button(BOARD_X + BOARD_SIZE + 140, 545, 100, 35, "Menu"),
            Button(BOARD_X + BOARD_SIZE + 30, 590, 100, 35, "Flip"),
            Button(BOARD_X + BOARD_SIZE + 140, 590, 100, 35, "Eval"),  # Toggle eval display
        ]

        self.difficulty_buttons = [
            Button(BOARD_X + BOARD_SIZE + 30, 400, 50, 30, "Easy"),
            Button(BOARD_X + BOARD_SIZE + 85, 400, 55, 30, "Med"),
            Button(BOARD_X + BOARD_SIZE + 145, 400, 50, 30, "Hard"),
            Button(BOARD_X + BOARD_SIZE + 200, 400, 45, 30, "Max"),
        ]

        self.review_buttons = [
            Button(BOARD_X + BOARD_SIZE + 30, 500, 50, 35, "<<"),
            Button(BOARD_X + BOARD_SIZE + 85, 500, 50, 35, "<"),
            Button(BOARD_X + BOARD_SIZE + 140, 500, 50, 35, ">"),
            Button(BOARD_X + BOARD_SIZE + 195, 500, 50, 35, ">>"),
            Button(BOARD_X + BOARD_SIZE + 30, 545, 215, 35, "Back to Menu"),
        ]

        self.puzzle_list_buttons: List[Button] = []
        self.opening_list_buttons: List[Button] = []
        self.endgame_list_buttons: List[Button] = []

        # Move quality badges
        self.current_badge: Optional[str] = None
        self.badge_surfaces = self._create_badge_surfaces()

    def _create_badge_surfaces(self) -> dict:
        """Create or load badge surfaces for move quality indicators."""
        import os
        badges = {}
        badge_size = 24

        # Badge configurations: (color, symbol)
        badge_config = {
            'best': ((76, 175, 80), '★'),      # Green
            'excellent': ((76, 175, 80), '✓'),  # Green
            'good': ((100, 149, 237), '●'),     # Blue
            'inaccuracy': ((255, 193, 7), '?'), # Yellow
            'mistake': ((255, 152, 0), '!'),    # Orange
            'blunder': ((244, 67, 54), '✗'),    # Red
        }

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(script_dir, 'assets', 'icons')

        for badge_type, (color, symbol) in badge_config.items():
            # Try to load custom image first
            image_path = os.path.join(icons_dir, f'{badge_type}.png')
            if os.path.exists(image_path):
                try:
                    img = pygame.image.load(image_path).convert_alpha()
                    badges[badge_type] = pygame.transform.smoothscale(img, (badge_size, badge_size))
                    continue
                except:
                    pass

            # Create default badge (colored circle with symbol)
            surface = pygame.Surface((badge_size, badge_size), pygame.SRCALPHA)

            # Draw circle background
            pygame.draw.circle(surface, color, (badge_size // 2, badge_size // 2), badge_size // 2)

            # Draw symbol
            font = pygame.font.SysFont('arial', 14, bold=True)
            text = font.render(symbol, True, (255, 255, 255))
            text_rect = text.get_rect(center=(badge_size // 2, badge_size // 2))
            surface.blit(text, text_rect)

            badges[badge_type] = surface

        return badges

    def run(self):
        """Main game loop."""
        import traceback
        while self.running:
            try:
                self._handle_events()
                self._update()
                self._draw()
                self.clock.tick(60)
            except Exception as e:
                print(f"ERROR: {e}")
                traceback.print_exc()
                self.message = f"Error: {e}"
                self.message_color = ERROR_COLOR

        # Clean up Stockfish engine before exit
        if self.ai.engine:
            try:
                self.ai.engine.quit()
            except:
                pass
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self._handle_click(event.pos)

    def _handle_mouse_motion(self, pos):
        """Handle mouse movement for button hover effects."""
        all_buttons = []
        if self.mode == GameMode.MENU:
            all_buttons = self.menu_buttons + self.puzzle_list_buttons + self.opening_list_buttons + self.endgame_list_buttons
        elif self.mode == GameMode.PLAY_VS_AI:
            all_buttons = self.game_buttons + self.difficulty_buttons
        elif self.mode == GameMode.PUZZLE:
            all_buttons = self.game_buttons[:4]  # Hint, Undo, New, Menu
        elif self.mode == GameMode.OPENING:
            all_buttons = self.game_buttons[2:4]  # New, Menu
        elif self.mode == GameMode.ENDGAME:
            all_buttons = self.game_buttons[:4]  # Hint, Undo, New, Menu
        elif self.mode == GameMode.REVIEW:
            all_buttons = self.review_buttons

        for btn in all_buttons:
            btn.update_hover(pos)

    def _handle_click(self, pos):
        """Handle mouse clicks."""
        if self.mode == GameMode.MENU:
            self._handle_menu_click(pos)
        elif self.mode == GameMode.PLAY_VS_AI:
            self._handle_game_click(pos)
        elif self.mode == GameMode.PUZZLE:
            self._handle_puzzle_click(pos)
        elif self.mode == GameMode.OPENING:
            self._handle_opening_click(pos)
        elif self.mode == GameMode.ENDGAME:
            self._handle_endgame_click(pos)
        elif self.mode == GameMode.REVIEW:
            self._handle_review_click(pos)

    def _handle_menu_click(self, pos):
        """Handle menu clicks."""
        for i, btn in enumerate(self.menu_buttons):
            if btn.is_clicked(pos):
                if i == 0:  # Play vs AI (new game)
                    self.paused_game = None  # Clear any paused game
                    self._clear_submenu_buttons()
                    self._start_game()
                elif i == 1:  # Resume Game
                    self._clear_submenu_buttons()
                    self._resume_game()
                elif i == 2:  # Puzzles
                    self.opening_list_buttons = []
                    self.endgame_list_buttons = []
                    self._show_puzzles()
                elif i == 3:  # Openings
                    self.puzzle_list_buttons = []
                    self.endgame_list_buttons = []
                    self._show_openings()
                elif i == 4:  # Endgames
                    self.puzzle_list_buttons = []
                    self.opening_list_buttons = []
                    self._show_endgames()
                elif i == 5:  # Review
                    self._clear_submenu_buttons()
                    self._start_review()
                elif i == 6:  # Quit
                    self.running = False
                return

        # Check puzzle selection
        for i, btn in enumerate(self.puzzle_list_buttons):
            if btn.is_clicked(pos):
                puzzles = self.puzzles.get_unsolved_puzzles()[:8]
                if i < len(puzzles):
                    self._start_puzzle(puzzles[i])
                return

        # Check opening selection
        for i, btn in enumerate(self.opening_list_buttons):
            if btn.is_clicked(pos):
                openings = self.openings.get_all_openings()
                if i < len(openings):
                    self._start_opening(openings[i])
                return

        # Check endgame selection
        for i, btn in enumerate(self.endgame_list_buttons):
            if btn.is_clicked(pos):
                endgames = self.endgames.get_all_endgames()
                if i < len(endgames):
                    self._start_endgame(endgames[i])
                return

    def _clear_submenu_buttons(self):
        """Clear all submenu button lists."""
        self.puzzle_list_buttons = []
        self.opening_list_buttons = []
        self.endgame_list_buttons = []

    def _handle_game_click(self, pos):
        """Handle game mode clicks."""
        # Check buttons
        for i, btn in enumerate(self.game_buttons):
            if btn.is_clicked(pos):
                if i == 0:  # Hint
                    self._show_hint()
                elif i == 1:  # Undo
                    self._undo_move()
                elif i == 2:  # New Game
                    self._start_game()
                elif i == 3:  # Menu
                    # Save game for review before going to menu
                    if self.game.move_history:
                        self.saved_game_moves = list(self.game.move_history)
                    # Save game state for resume (if not game over)
                    if not self.game_over and self.game.move_history:
                        self.paused_game = {
                            'fen': self.game.board.fen(),
                            'moves': list(self.game.move_history),
                            'player_color': self.player_color,
                            'last_move': self.board_view.last_move
                        }
                    self.mode = GameMode.MENU
                elif i == 4:  # Flip
                    self.board_view.flip()
                elif i == 5:  # Eval toggle
                    self.show_eval = not self.show_eval
                    if self.show_eval:
                        self._update_eval()
                        self.message = "Evaluation display ON"
                    else:
                        self.message = "Evaluation display OFF"
                return

        for i, btn in enumerate(self.difficulty_buttons):
            if btn.is_clicked(pos):
                diff = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD, Difficulty.STOCKFISH][i]
                self.ai.set_difficulty(diff)
                name = "Stockfish Max" if diff == Difficulty.STOCKFISH else diff.name
                self.message = f"Difficulty: {name}" + (" (Stockfish)" if self.ai.has_stockfish() and diff != Difficulty.EASY else "")
                return

        # Handle board clicks
        if not self.game_over and self.game.get_turn() == self.player_color:
            self._handle_board_click(pos)

    def _handle_puzzle_click(self, pos):
        """Handle puzzle mode clicks."""
        # Buttons
        for i, btn in enumerate(self.game_buttons[:4]):
            if btn.is_clicked(pos):
                if i == 0:  # Hint
                    hint = self.puzzles.get_hint()
                    if hint:
                        self.message = hint
                elif i == 1:  # Skip
                    self._show_puzzles()
                elif i == 2:  # New puzzle
                    self._show_puzzles()
                elif i == 3:  # Menu
                    self.mode = GameMode.MENU
                    self.puzzle_list_buttons = []
                return

        # Board
        self._handle_board_click(pos)

    def _handle_opening_click(self, pos):
        """Handle opening trainer clicks."""
        for i, btn in enumerate(self.game_buttons[2:4]):
            if btn.is_clicked(pos):
                if i == 0:  # New
                    self._show_openings()
                elif i == 1:  # Menu
                    self.mode = GameMode.MENU
                    self.opening_list_buttons = []
                return

        self._handle_board_click(pos)

    def _handle_endgame_click(self, pos):
        """Handle endgame trainer clicks."""
        for i, btn in enumerate(self.game_buttons[:4]):
            if btn.is_clicked(pos):
                if i == 0:  # Hint
                    hint = self.endgames.get_hint()
                    if hint:
                        self.message = hint
                        self.message_color = ACCENT_COLOR
                elif i == 1:  # Reset
                    if self.current_endgame:
                        self._start_endgame(self.current_endgame)
                elif i == 2:  # New
                    self._show_endgames()
                elif i == 3:  # Menu
                    self.mode = GameMode.MENU
                    self.endgame_list_buttons = []
                return

        self._handle_board_click(pos)

    def _handle_review_click(self, pos):
        """Handle review mode clicks."""
        for i, btn in enumerate(self.review_buttons):
            if btn.is_clicked(pos):
                if i == 0:  # First
                    fen = self.reviewer.first_move()
                    self.game.load_fen(fen)
                elif i == 1:  # Prev
                    fen = self.reviewer.prev_move()
                    if fen:
                        self.game.load_fen(fen)
                elif i == 2:  # Next
                    result = self.reviewer.next_move()
                    if result:
                        fen, analysis = result
                        self.game.load_fen(fen)
                        if analysis:
                            self.message = f"{analysis.san}: {analysis.classification} - {analysis.explanation}"
                elif i == 3:  # Last
                    fen = self.reviewer.last_move()
                    self.game.load_fen(fen)
                elif i == 4:  # Menu
                    self.mode = GameMode.MENU
                return

    def _handle_board_click(self, pos):
        """Handle clicks on the chess board."""
        square = self.board_view.pixel_to_square(pos[0], pos[1])
        if square is None:
            return

        if self.selected_square is None:
            # Select a piece
            piece = self.game.get_piece_at(square)
            if piece and piece.color == self.game.get_turn():
                self.selected_square = square
                self.board_view.set_selected(square)
                legal_targets = [m.to_square for m in self.game.get_legal_moves_for_square(square)]
                self.board_view.set_highlights(legal_targets)
                self.board_view.clear_hints()  # Clear hints when selecting a piece
        else:
            # Try to make a move
            move = None
            for m in self.game.get_legal_moves_for_square(self.selected_square):
                if m.to_square == square:
                    # Handle promotion
                    if m.promotion:
                        move = chess.Move(self.selected_square, square, chess.QUEEN)
                    else:
                        move = m
                    break

            if move and move in self.game.board.legal_moves:
                self._make_move(move)

            # Clear selection and hints
            self.selected_square = None
            self.board_view.set_selected(None)
            self.board_view.set_highlights([])
            self.board_view.clear_hints()

    def _make_move(self, move: chess.Move):
        """Make a move and handle mode-specific logic."""
        if self.mode == GameMode.PLAY_VS_AI:
            # Get move quality explanation BEFORE making the move
            badge_type, explanation = self.hints.explain_move_quality(self.game.board, move)
            self.current_badge = badge_type
            self.message = explanation
            self.game.make_move(move)
            self.board_view.set_last_move(move)

            # Update evaluation if enabled
            if self.show_eval:
                self._update_eval()

            if self.game.is_game_over():
                self.game_over = True
                self.message = self.game.get_game_result() or "Game Over"
                # Save game for review
                if self.game.move_history:
                    self.saved_game_moves = list(self.game.move_history)
                self.paused_game = None  # Clear paused game on game over
            else:
                self.ai_thinking = True

        elif self.mode == GameMode.PUZZLE:
            correct, msg = self.puzzles.check_move(self.game.board, move)
            self.message = msg
            self.message_color = SUCCESS_COLOR if correct else ERROR_COLOR
            if correct and self.puzzles.practice_board:
                # Sync board with puzzle manager's board
                self.game.board = self.puzzles.practice_board.copy()
                self.board_view.set_last_move(move)

        elif self.mode == GameMode.OPENING:
            correct, msg = self.openings.check_move(move)
            self.message = msg
            self.message_color = SUCCESS_COLOR if correct else ERROR_COLOR
            if correct:
                self.game.board = self.openings.practice_board.copy()
                self.board_view.set_last_move(move)
                # Show key idea
                idea = self.openings.get_current_idea()
                if idea:
                    self.message += f" | Tip: {idea}"

        elif self.mode == GameMode.ENDGAME:
            success, msg = self.endgames.make_move(move)
            self.message = msg
            self.message_color = SUCCESS_COLOR if success else ERROR_COLOR
            if self.endgames.practice_board:
                self.game.board = self.endgames.practice_board.copy()
                self.board_view.set_last_move(move)

    def _update(self):
        """Update game state."""
        if self.mode == GameMode.PLAY_VS_AI and self.ai_thinking:
            if not self.game_over and self.game.get_turn() != self.player_color:
                ai_move = self.ai.get_best_move(self.game.board)
                if ai_move:
                    self.game.make_move(ai_move)
                    self.board_view.set_last_move(ai_move)

                    # Update evaluation if enabled
                    if self.show_eval:
                        self._update_eval()

                    if self.game.is_game_over():
                        self.game_over = True
                        self.message = self.game.get_game_result() or "Game Over"
                        # Save game for review
                        if self.game.move_history:
                            self.saved_game_moves = list(self.game.move_history)
                        self.paused_game = None  # Clear paused game on game over

            self.ai_thinking = False

    def _draw(self):
        """Draw the current frame."""
        self.screen.fill(BG_COLOR)

        if self.mode == GameMode.MENU:
            self._draw_menu()
        elif self.mode in [GameMode.PLAY_VS_AI, GameMode.PUZZLE, GameMode.OPENING, GameMode.ENDGAME, GameMode.REVIEW]:
            self._draw_game()

        pygame.display.flip()

    def _draw_menu(self):
        """Draw the main menu."""
        # Title
        title = self.title_font.render("Chess Learner", True, ACCENT_COLOR)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 80))

        subtitle = self.font.render("Learn chess through play, puzzles, and analysis", True, TEXT_COLOR)
        self.screen.blit(subtitle, (WINDOW_WIDTH // 2 - subtitle.get_width() // 2, 130))

        # Buttons
        for i, btn in enumerate(self.menu_buttons):
            # Draw Resume Game button differently if no paused game
            if i == 1:  # Resume Game button
                if self.paused_game:
                    btn.draw(self.screen, self.font)
                    # Add indicator that game is paused
                    pygame.draw.rect(self.screen, SUCCESS_COLOR, btn.rect, 2, border_radius=5)
                else:
                    # Draw disabled button
                    pygame.draw.rect(self.screen, (50, 50, 55), btn.rect, border_radius=5)
                    pygame.draw.rect(self.screen, (80, 80, 90), btn.rect, 2, border_radius=5)
                    text_surface = self.font.render(btn.text, True, (100, 100, 100))
                    text_rect = text_surface.get_rect(center=btn.rect.center)
                    self.screen.blit(text_surface, text_rect)
            else:
                btn.draw(self.screen, self.font)

        # Show puzzle/opening/endgame lists if active
        for btn in self.puzzle_list_buttons:
            btn.draw(self.screen, self.small_font)
        for btn in self.opening_list_buttons:
            btn.draw(self.screen, self.small_font)
        for btn in self.endgame_list_buttons:
            btn.draw(self.screen, self.small_font)

    def _draw_game(self):
        """Draw the game view."""
        # Title
        mode_titles = {
            GameMode.PLAY_VS_AI: "Play vs Computer",
            GameMode.PUZZLE: f"Puzzle: {self.current_puzzle.name if self.current_puzzle else ''}",
            GameMode.OPENING: f"Opening: {self.current_opening.name if self.current_opening else ''}",
            GameMode.ENDGAME: f"Endgame: {self.current_endgame.name if self.current_endgame else ''}",
            GameMode.REVIEW: "Game Review"
        }
        title = self.title_font.render(mode_titles.get(self.mode, ""), True, ACCENT_COLOR)
        self.screen.blit(title, (BOARD_X, 20))

        # Draw board
        self.board_view.draw(self.screen, self.game.board)

        # Side panel
        panel_x = BOARD_X + BOARD_SIZE + 20
        pygame.draw.rect(self.screen, PANEL_COLOR,
                        (panel_x, BOARD_Y, 250, BOARD_SIZE), border_radius=10)

        # Turn indicator
        turn_text = "White to move" if self.game.get_turn() else "Black to move"
        if self.game.is_check():
            turn_text += " (CHECK!)"
        turn_surface = self.font.render(turn_text, True, TEXT_COLOR)
        self.screen.blit(turn_surface, (panel_x + 10, BOARD_Y + 10))

        # Track vertical offset for dynamic layout
        content_y = BOARD_Y + 35

        # Evaluation bar (if enabled)
        if self.show_eval and self.mode == GameMode.PLAY_VS_AI:
            bar_width = 230
            bar_height = 18

            # Background (black side)
            pygame.draw.rect(self.screen, (60, 60, 60),
                           (panel_x + 10, content_y, bar_width, bar_height))

            # White portion based on win probability
            white_width = int(bar_width * self.white_win_prob / 100)
            pygame.draw.rect(self.screen, (240, 240, 240),
                           (panel_x + 10, content_y, white_width, bar_height))

            # Border
            pygame.draw.rect(self.screen, (100, 100, 100),
                           (panel_x + 10, content_y, bar_width, bar_height), 2)

            content_y += bar_height + 3

            # Eval text
            eval_text = self.small_font.render(f"Eval: {self.current_eval}  ({self.white_win_prob}% white)", True, TEXT_COLOR)
            self.screen.blit(eval_text, (panel_x + 10, content_y))
            content_y += 18

            # Eval reason
            if self.eval_reason:
                reason_text = self.small_font.render(self.eval_reason, True, (180, 180, 200))
                self.screen.blit(reason_text, (panel_x + 10, content_y))
                content_y += 18

            content_y += 5  # Add some spacing after eval section

        # Message with badge
        if self.message:
            badge_offset = 0

            # Draw badge if in Play vs AI mode and badge exists
            if self.mode == GameMode.PLAY_VS_AI and self.current_badge and self.current_badge in self.badge_surfaces:
                badge = self.badge_surfaces[self.current_badge]
                self.screen.blit(badge, (panel_x + 10, content_y))
                badge_offset = 30  # Space for badge

            # Word wrap message
            words = self.message.split()
            lines = []
            current_line = ""
            max_width = 200 if badge_offset else 230
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if self.small_font.size(test_line)[0] < max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            max_lines = 3 if self.show_eval else 4
            for i, line in enumerate(lines[:max_lines]):
                msg_surface = self.small_font.render(line, True, self.message_color)
                x_pos = panel_x + 10 + (badge_offset if i == 0 else 0)
                self.screen.blit(msg_surface, (x_pos, content_y + i * 18))
            content_y += max_lines * 18 + 5

        # Move history - position based on content above
        history_y = max(content_y, BOARD_Y + 130)
        history_label = self.font.render("Moves:", True, TEXT_COLOR)
        self.screen.blit(history_label, (panel_x + 10, history_y))

        # Show last 10 moves
        moves = self.game.move_history[-20:]
        temp_board = chess.Board()
        for m in self.game.move_history[:-20]:
            temp_board.push(m)

        move_text = ""
        for i, move in enumerate(moves):
            if (len(self.game.move_history) - 20 + i) % 2 == 0:
                move_num = (len(self.game.move_history) - 20 + i) // 2 + 1
                move_text += f"{move_num}. "
            move_text += temp_board.san(move) + " "
            temp_board.push(move)

        # Wrap move text
        move_lines = []
        current_line = ""
        for word in move_text.split():
            test_line = current_line + " " + word if current_line else word
            if self.small_font.size(test_line)[0] < 220:
                current_line = test_line
            else:
                move_lines.append(current_line)
                current_line = word
        if current_line:
            move_lines.append(current_line)

        for i, line in enumerate(move_lines[:8]):
            move_surface = self.small_font.render(line, True, (180, 180, 180))
            self.screen.blit(move_surface, (panel_x + 10, history_y + 25 + i * 18))

        # Draw appropriate buttons
        if self.mode == GameMode.PLAY_VS_AI:
            # Difficulty label
            diff_label = self.font.render("Difficulty:", True, TEXT_COLOR)
            self.screen.blit(diff_label, (panel_x + 10, 375))

            for i, btn in enumerate(self.difficulty_buttons):
                btn.draw(self.screen, self.small_font)
                # Highlight current difficulty
                if (i == 0 and self.ai.difficulty == Difficulty.EASY or
                    i == 1 and self.ai.difficulty == Difficulty.MEDIUM or
                    i == 2 and self.ai.difficulty == Difficulty.HARD or
                    i == 3 and self.ai.difficulty == Difficulty.STOCKFISH):
                    pygame.draw.rect(self.screen, SUCCESS_COLOR, btn.rect, 2, border_radius=5)

            for i, btn in enumerate(self.game_buttons):
                btn.draw(self.screen, self.small_font)
                # Highlight Eval button if enabled
                if i == 5 and self.show_eval:
                    pygame.draw.rect(self.screen, SUCCESS_COLOR, btn.rect, 2, border_radius=5)

        elif self.mode == GameMode.PUZZLE:
            for btn in self.game_buttons[:4]:
                btn.draw(self.screen, self.small_font)

            # Puzzle progress
            solved, total = self.puzzles.get_progress()
            progress = self.font.render(f"Solved: {solved}/{total}", True, TEXT_COLOR)
            self.screen.blit(progress, (panel_x + 10, 450))

        elif self.mode == GameMode.OPENING:
            for btn in self.game_buttons[2:4]:
                btn.draw(self.screen, self.small_font)

            # Show opening info
            if self.current_opening:
                info_y = 400
                desc = self.small_font.render(self.current_opening.description[:50] + "...", True, TEXT_COLOR)
                self.screen.blit(desc, (panel_x + 10, info_y))

                hint = self.openings.get_next_move_hint()
                if hint:
                    hint_surface = self.font.render(hint, True, ACCENT_COLOR)
                    self.screen.blit(hint_surface, (panel_x + 10, info_y + 30))

        elif self.mode == GameMode.ENDGAME:
            for btn in self.game_buttons[:4]:
                btn.draw(self.screen, self.small_font)

            # Show endgame info
            if self.current_endgame:
                info_y = 400
                goal = self.small_font.render(f"Goal: {self.current_endgame.goal}", True, ACCENT_COLOR)
                self.screen.blit(goal, (panel_x + 10, info_y))

                progress = self.endgames.get_progress_message()
                if progress:
                    prog_surface = self.small_font.render(progress, True, TEXT_COLOR)
                    self.screen.blit(prog_surface, (panel_x + 10, info_y + 25))

        elif self.mode == GameMode.REVIEW:
            for btn in self.review_buttons:
                btn.draw(self.screen, self.small_font)

            # Show analysis
            analysis = self.reviewer.get_current_analysis()
            if analysis:
                class_color = {
                    'best': SUCCESS_COLOR,
                    'good': (150, 200, 150),
                    'inaccuracy': (200, 200, 100),
                    'mistake': (200, 150, 100),
                    'blunder': ERROR_COLOR
                }.get(analysis.classification, TEXT_COLOR)

                class_text = self.font.render(f"{analysis.san}: {analysis.classification.upper()}", True, class_color)
                self.screen.blit(class_text, (panel_x + 10, 440))

                if analysis.best_move_san and analysis.best_move_san != analysis.san:
                    better = self.small_font.render(f"Better: {analysis.best_move_san}", True, TEXT_COLOR)
                    self.screen.blit(better, (panel_x + 10, 465))

    def _resume_game(self):
        """Resume a paused game."""
        if not self.paused_game:
            self.message = "No game to resume! Start a new game."
            return

        self.mode = GameMode.PLAY_VS_AI
        self.game.board = chess.Board(self.paused_game['fen'])
        self.game.move_history = list(self.paused_game['moves'])
        self.player_color = self.paused_game['player_color']
        self.board_view.set_last_move(self.paused_game['last_move'])
        self.board_view.set_selected(None)
        self.board_view.set_highlights([])
        self.board_view.clear_hints()
        self.selected_square = None
        self.message = "Game resumed. Your turn!" if self.game.get_turn() == self.player_color else "Game resumed."
        self.message_color = TEXT_COLOR
        self.game_over = False
        self.ai_thinking = self.game.get_turn() != self.player_color
        self.puzzle_list_buttons = []
        self.opening_list_buttons = []
        # Update eval if enabled
        if self.show_eval:
            self._update_eval()

    def _start_game(self):
        """Start a new game vs AI."""
        # Save current game for review (if any moves were made)
        if self.game.move_history:
            self.saved_game_moves = list(self.game.move_history)
        self.mode = GameMode.PLAY_VS_AI
        self.game.reset()
        self.board_view.set_last_move(None)
        self.board_view.set_selected(None)
        self.board_view.set_highlights([])
        self.board_view.clear_hints()
        self.selected_square = None
        self.message = "Your turn! You play as White."
        self.message_color = TEXT_COLOR
        self.player_color = chess.WHITE
        self.game_over = False
        self.ai_thinking = False
        self.puzzle_list_buttons = []
        self.opening_list_buttons = []
        # Reset evaluation
        self.current_eval = "0.00"
        self.white_win_prob = 50
        self.eval_reason = "Starting position"
        self.current_badge = None

    def _show_puzzles(self):
        """Show puzzle selection."""
        self.mode = GameMode.MENU
        puzzles = self.puzzles.get_unsolved_puzzles()[:8]

        self.puzzle_list_buttons = []
        for i, puzzle in enumerate(puzzles):
            btn = Button(WINDOW_WIDTH // 2 + 150, 200 + i * 45, 200, 40,
                        f"{puzzle.name} ({puzzle.theme})")
            self.puzzle_list_buttons.append(btn)

        self.opening_list_buttons = []

    def _start_puzzle(self, puzzle: Puzzle):
        """Start a puzzle."""
        self.mode = GameMode.PUZZLE
        self.current_puzzle = puzzle
        board = self.puzzles.start_puzzle(puzzle)
        self.game.board = board.copy()
        self.board_view.set_last_move(None)
        self.selected_square = None
        self.message = puzzle.description
        self.message_color = TEXT_COLOR
        self.puzzle_list_buttons = []

    def _show_openings(self):
        """Show opening selection."""
        self.mode = GameMode.MENU
        openings = self.openings.get_all_openings()[:8]

        self.opening_list_buttons = []
        for i, opening in enumerate(openings):
            btn = Button(WINDOW_WIDTH // 2 + 150, 200 + i * 45, 200, 40, opening.name)
            self.opening_list_buttons.append(btn)

        self.puzzle_list_buttons = []

    def _start_opening(self, opening: Opening):
        """Start opening practice."""
        self.mode = GameMode.OPENING
        self.current_opening = opening
        board = self.openings.start_practice(opening, play_as_white=True)
        self.game.board = board.copy()
        self.board_view.set_last_move(None)
        self.selected_square = None
        self.message = f"Practice the {opening.name}. {opening.description}"
        self.message_color = TEXT_COLOR
        self.opening_list_buttons = []

    def _show_endgames(self):
        """Show endgame selection."""
        self.mode = GameMode.MENU
        endgames = self.endgames.get_all_endgames()[:8]

        self.endgame_list_buttons = []
        for i, endgame in enumerate(endgames):
            btn = Button(WINDOW_WIDTH // 2 + 150, 160 + i * 42, 200, 38, endgame.name)
            self.endgame_list_buttons.append(btn)

        self.puzzle_list_buttons = []
        self.opening_list_buttons = []

    def _start_endgame(self, endgame: Endgame):
        """Start endgame practice."""
        self.mode = GameMode.ENDGAME
        self.current_endgame = endgame
        board = self.endgames.start_practice(endgame)
        self.game.board = board.copy()
        self.board_view.set_last_move(None)
        self.selected_square = None
        self.message = endgame.description
        self.message_color = TEXT_COLOR
        self.endgame_list_buttons = []

    def _start_review(self):
        """Start game review."""
        # Use current game if it has moves, otherwise use saved game
        moves_to_review = list(self.game.move_history) if self.game.move_history else self.saved_game_moves

        if not moves_to_review:
            self.message = "No game to review! Play a game first."
            return

        self.mode = GameMode.REVIEW
        self.reviewer.analyze_game(moves_to_review)
        self.game.board = chess.Board()  # Start from beginning
        self.board_view.set_last_move(None)
        self.message = f"Reviewing game ({len(moves_to_review)} moves). Use arrows to navigate."
        self.message_color = TEXT_COLOR

    def _show_hint(self):
        """Show a hint for the current position."""
        if self.game_over:
            return

        move, explanation = self.hints.get_best_move_hint(self.game.board)
        if move:
            self.board_view.set_hints([move.from_square, move.to_square])
            self.message = f"Try: {self.game.board.san(move)} - {explanation}"
            self.message_color = ACCENT_COLOR

    def _undo_move(self):
        """Undo the last move (and AI's response)."""
        if self.mode != GameMode.PLAY_VS_AI:
            return

        # Undo AI move
        if self.game.move_history and self.game.get_turn() == self.player_color:
            self.game.undo_move()

        # Undo player move
        if self.game.move_history:
            self.game.undo_move()

        self.board_view.set_last_move(
            self.game.move_history[-1] if self.game.move_history else None
        )
        self.game_over = False
        self.message = "Move undone. Your turn."
        if self.show_eval:
            self._update_eval()

    def _update_eval(self):
        """Update position evaluation using Stockfish."""
        if not self.ai.engine:
            self.current_eval = "N/A"
            self.white_win_prob = 50
            self.eval_reason = "Engine not available"
            return

        try:
            info = self.ai.engine.analyse(self.game.board, chess.engine.Limit(time=0.1))
            score = info.get("score")

            if score:
                if score.is_mate():
                    mate_in = score.white().mate()
                    if mate_in > 0:
                        self.current_eval = f"M{mate_in}"
                        self.white_win_prob = 100
                        self.eval_reason = f"White mates in {mate_in}"
                    else:
                        self.current_eval = f"M{mate_in}"
                        self.white_win_prob = 0
                        self.eval_reason = f"Black mates in {abs(mate_in)}"
                else:
                    cp = score.white().score()
                    if cp is not None:
                        self.current_eval = f"{cp/100:+.2f}"
                        # Convert centipawns to win probability (sigmoid approximation)
                        self.white_win_prob = int(50 + 50 * (2 / (1 + 10**(-cp/400)) - 1))
                        self.white_win_prob = max(0, min(100, self.white_win_prob))
                        # Compute reason
                        self.eval_reason = self._compute_eval_reason(cp)
                    else:
                        self.current_eval = "0.00"
                        self.white_win_prob = 50
                        self.eval_reason = "Equal position"
            else:
                self.current_eval = "0.00"
                self.white_win_prob = 50
                self.eval_reason = "Equal position"
        except Exception as e:
            self.current_eval = "?"
            self.white_win_prob = 50
            self.eval_reason = ""

    def _compute_eval_reason(self, cp: int) -> str:
        """Compute a reason for the evaluation based on position features."""
        board = self.game.board
        reasons = []

        # Material count
        piece_values = {
            chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
            chess.ROOK: 500, chess.QUEEN: 900
        }

        white_material = sum(
            len(board.pieces(pt, chess.WHITE)) * val
            for pt, val in piece_values.items()
        )
        black_material = sum(
            len(board.pieces(pt, chess.BLACK)) * val
            for pt, val in piece_values.items()
        )
        material_diff = white_material - black_material

        if abs(material_diff) >= 300:
            if material_diff > 0:
                reasons.append("White up material")
            else:
                reasons.append("Black up material")

        # Check status
        if board.is_check():
            reasons.append("In check")

        # Piece activity (simple: count attacked squares)
        if not reasons:
            # Center control
            center_squares = [chess.E4, chess.D4, chess.E5, chess.D5]
            white_center = sum(1 for sq in center_squares if board.is_attacked_by(chess.WHITE, sq))
            black_center = sum(1 for sq in center_squares if board.is_attacked_by(chess.BLACK, sq))

            if white_center > black_center + 1:
                reasons.append("White controls center")
            elif black_center > white_center + 1:
                reasons.append("Black controls center")

        # King safety (simple check for castling rights or king position)
        if not reasons:
            if abs(cp) > 50:
                if cp > 0:
                    reasons.append("White has advantage")
                else:
                    reasons.append("Black has advantage")
            else:
                reasons.append("Equal position")

        return reasons[0] if reasons else "Balanced"


if __name__ == "__main__":
    # Check for existing instance
    lock_socket = acquire_lock()
    if lock_socket is None:
        print("Chess Learner is already running!")
        # Show a message box if pygame can init
        try:
            pygame.init()
            pygame.display.set_mode((300, 100))
            pygame.display.set_caption("Chess Learner")
            font = pygame.font.SysFont('arial', 16)
            screen = pygame.display.get_surface()
            screen.fill((50, 50, 55))
            text = font.render("Chess Learner is already running!", True, (220, 220, 220))
            screen.blit(text, (20, 40))
            pygame.display.flip()
            pygame.time.wait(2000)
            pygame.quit()
        except:
            pass
        sys.exit(1)

    try:
        app = ChessLearner()
        app.run()
    finally:
        lock_socket.close()
