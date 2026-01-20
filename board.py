"""Chess board rendering using Pygame with image or Unicode symbol pieces."""
import pygame
import chess
import os
from typing import Optional, List, Tuple, Set

# Colors
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_YELLOW = (247, 247, 105, 180)
HIGHLIGHT_GREEN = (106, 168, 79, 180)
HINT_BLUE = (66, 135, 245, 150)
LAST_MOVE_HIGHLIGHT = (255, 255, 0, 100)


class ChessBoard:
    """Handles chess board rendering with Unicode symbol pieces."""

    def __init__(self, x: int, y: int, square_size: int = 80):
        self.x = x
        self.y = y
        self.square_size = square_size
        self.flipped = False
        self.selected_square: Optional[int] = None
        self.highlighted_squares: Set[int] = set()
        self.hint_squares: Set[int] = set()
        self.last_move: Optional[chess.Move] = None
        self.piece_surfaces: dict = {}

        pygame.font.init()
        self.label_font = pygame.font.SysFont('arial', 14)

        # Try fonts that have good chess symbols
        font_size = int(square_size * 0.8)
        self.piece_font = None
        for font_name in ['Apple Symbols', 'Arial Unicode MS', 'Segoe UI Symbol', 'DejaVu Sans', None]:
            try:
                self.piece_font = pygame.font.SysFont(font_name, font_size)
                if self.piece_font:
                    break
            except:
                continue

        if not self.piece_font:
            self.piece_font = pygame.font.Font(None, font_size)

        self._create_piece_surfaces()

    def _create_piece_surfaces(self):
        """Load piece graphics from images, falling back to Unicode symbols."""
        size = self.square_size

        # Try to load from image files first
        piece_names = {
            chess.KING: 'king',
            chess.QUEEN: 'queen',
            chess.ROOK: 'rook',
            chess.BISHOP: 'bishop',
            chess.KNIGHT: 'knight',
            chess.PAWN: 'pawn',
        }

        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, 'assets', 'pieces')

        images_loaded = 0
        for color in [chess.WHITE, chess.BLACK]:
            color_name = 'white' if color == chess.WHITE else 'black'
            for piece_type, piece_name in piece_names.items():
                # Try to load image file
                image_path = os.path.join(assets_dir, f'{color_name}_{piece_name}.png')
                if os.path.exists(image_path):
                    try:
                        img = pygame.image.load(image_path).convert_alpha()
                        # Scale to fit square size with some padding
                        img = pygame.transform.smoothscale(img, (size - 8, size - 8))
                        # Center on a square-sized surface
                        surface = pygame.Surface((size, size), pygame.SRCALPHA)
                        surface.blit(img, (4, 4))
                        self.piece_surfaces[(color, piece_type)] = surface
                        images_loaded += 1
                    except Exception as e:
                        print(f"Failed to load {image_path}: {e}")

        if images_loaded > 0:
            print(f"Loaded {images_loaded}/12 piece images from assets/pieces/")

        # Fall back to Unicode for any missing pieces
        self._create_unicode_fallbacks()

    def _create_unicode_fallbacks(self):
        """Create Unicode symbol surfaces for any missing pieces."""
        size = self.square_size

        # Unicode chess pieces
        symbols = {
            (chess.WHITE, chess.KING): '\u2654',
            (chess.WHITE, chess.QUEEN): '\u2655',
            (chess.WHITE, chess.ROOK): '\u2656',
            (chess.WHITE, chess.BISHOP): '\u2657',
            (chess.WHITE, chess.KNIGHT): '\u2658',
            (chess.WHITE, chess.PAWN): '\u2659',
            (chess.BLACK, chess.KING): '\u265A',
            (chess.BLACK, chess.QUEEN): '\u265B',
            (chess.BLACK, chess.ROOK): '\u265C',
            (chess.BLACK, chess.BISHOP): '\u265D',
            (chess.BLACK, chess.KNIGHT): '\u265E',
            (chess.BLACK, chess.PAWN): '\u265F',
        }

        for (color, piece_type), symbol in symbols.items():
            # Skip if already loaded from image
            if (color, piece_type) in self.piece_surfaces:
                continue

            surface = pygame.Surface((size, size), pygame.SRCALPHA)

            # Colors with outline for visibility
            text_color = (255, 255, 255) if color == chess.WHITE else (30, 30, 30)
            outline_color = (0, 0, 0) if color == chess.WHITE else (220, 220, 220)

            # Draw outline by rendering in multiple offset positions
            for dx, dy in [(-2,0), (2,0), (0,-2), (0,2), (-1,-1), (1,-1), (-1,1), (1,1)]:
                outline_surf = self.piece_font.render(symbol, True, outline_color)
                rect = outline_surf.get_rect(center=(size//2 + dx, size//2 + dy))
                surface.blit(outline_surf, rect)

            # Draw main piece
            piece_surf = self.piece_font.render(symbol, True, text_color)
            rect = piece_surf.get_rect(center=(size//2, size//2))
            surface.blit(piece_surf, rect)

            self.piece_surfaces[(color, piece_type)] = surface

    def get_board_size(self) -> int:
        """Get total board size."""
        return self.square_size * 8

    def square_to_pixel(self, square: int) -> Tuple[int, int]:
        """Convert chess square to pixel coordinates."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        if self.flipped:
            px = self.x + (7 - file) * self.square_size
            py = self.y + rank * self.square_size
        else:
            px = self.x + file * self.square_size
            py = self.y + (7 - rank) * self.square_size

        return px, py

    def pixel_to_square(self, px: int, py: int) -> Optional[int]:
        """Convert pixel coordinates to chess square."""
        if not (self.x <= px < self.x + 8 * self.square_size and
                self.y <= py < self.y + 8 * self.square_size):
            return None

        file = (px - self.x) // self.square_size
        rank = 7 - (py - self.y) // self.square_size

        if self.flipped:
            file = 7 - file
            rank = 7 - rank

        return chess.square(file, rank)

    def draw(self, surface: pygame.Surface, board: chess.Board):
        """Draw the chess board and pieces."""
        self._draw_squares(surface)
        self._draw_highlights(surface)
        self._draw_pieces(surface, board)
        self._draw_labels(surface)

    def _draw_squares(self, surface: pygame.Surface):
        """Draw the board squares."""
        for square in chess.SQUARES:
            px, py = self.square_to_pixel(square)
            file = chess.square_file(square)
            rank = chess.square_rank(square)

            is_light = (file + rank) % 2 == 1
            color = LIGHT_SQUARE if is_light else DARK_SQUARE

            pygame.draw.rect(surface, color,
                           (px, py, self.square_size, self.square_size))

    def _draw_highlights(self, surface: pygame.Surface):
        """Draw square highlights."""
        # Last move highlight
        if self.last_move:
            for sq in [self.last_move.from_square, self.last_move.to_square]:
                px, py = self.square_to_pixel(sq)
                highlight_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
                highlight_surface.fill(LAST_MOVE_HIGHLIGHT)
                surface.blit(highlight_surface, (px, py))

        # Selected square
        if self.selected_square is not None:
            px, py = self.square_to_pixel(self.selected_square)
            highlight_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            highlight_surface.fill(HIGHLIGHT_YELLOW)
            surface.blit(highlight_surface, (px, py))

        # Legal move highlights
        for sq in self.highlighted_squares:
            px, py = self.square_to_pixel(sq)
            highlight_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            highlight_surface.fill(HIGHLIGHT_GREEN)
            surface.blit(highlight_surface, (px, py))

        # Hint squares
        for sq in self.hint_squares:
            px, py = self.square_to_pixel(sq)
            hint_surface = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            pygame.draw.circle(hint_surface, HINT_BLUE,
                             (self.square_size // 2, self.square_size // 2),
                             self.square_size // 6)
            surface.blit(hint_surface, (px, py))

    def _draw_pieces(self, surface: pygame.Surface, board: chess.Board):
        """Draw all pieces on the board."""
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                px, py = self.square_to_pixel(square)
                key = (piece.color, piece.piece_type)
                piece_surface = self.piece_surfaces.get(key)
                if piece_surface:
                    surface.blit(piece_surface, (px, py))

    def _draw_labels(self, surface: pygame.Surface):
        """Draw file and rank labels."""
        label_color = (100, 100, 100)
        files = 'abcdefgh' if not self.flipped else 'hgfedcba'
        ranks = '12345678' if not self.flipped else '87654321'

        for i, f in enumerate(files):
            text = self.label_font.render(f, True, label_color)
            x = self.x + i * self.square_size + self.square_size // 2 - text.get_width() // 2
            y = self.y + 8 * self.square_size + 5
            surface.blit(text, (x, y))

        for i, r in enumerate(ranks):
            text = self.label_font.render(r, True, label_color)
            x = self.x - 20
            y = self.y + i * self.square_size + self.square_size // 2 - text.get_height() // 2
            surface.blit(text, (x, y))

    def set_selected(self, square: Optional[int]):
        """Set the selected square."""
        self.selected_square = square

    def set_highlights(self, squares: List[int]):
        """Set highlighted squares (legal moves)."""
        self.highlighted_squares = set(squares)

    def set_hints(self, squares: List[int]):
        """Set hint squares."""
        self.hint_squares = set(squares)

    def clear_hints(self):
        """Clear all hints."""
        self.hint_squares.clear()

    def set_last_move(self, move: Optional[chess.Move]):
        """Set the last move for highlighting."""
        self.last_move = move

    def flip(self):
        """Flip the board orientation."""
        self.flipped = not self.flipped
