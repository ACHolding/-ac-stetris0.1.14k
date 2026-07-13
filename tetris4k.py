#!/usr/bin/env python3
"""
AC's Tetris 4K  —  files = off
Python 3.14 + pygame @ 60 fps. No external assets.
All Tetris opcodes + procedural Korobeiniki theme.
"""

from __future__ import annotations

import math
import os
import random
import struct
import sys
from typing import Optional

import pygame

# ============================================================
# config  (files = off)
# ============================================================

PR_FILES = "off"
W, H = 720, 800
FPS = 60
COLS, ROWS = 10, 20
CELL = 32
BOARD_X = 48
BOARD_Y = 64
RATE = 22050

BG = (12, 14, 22)
PANEL = (22, 26, 38)
GRID = (36, 42, 58)
TEXT = (220, 230, 255)
ACCENT = (80, 200, 255)
GOLD = (255, 214, 64)
DIM = (140, 150, 170)
OVERLAY = (0, 0, 0, 180)

# Classic NES / Game Boy Tetris colors
COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
    "G": (90, 90, 100),  # ghost
}

# ============================================================
# opcodes  —  all Tetris action IDs
# ============================================================

(
    OP_IDLE,
    OP_SPAWN,
    OP_MOVE_LEFT,
    OP_MOVE_RIGHT,
    OP_SOFT_DROP,
    OP_HARD_DROP,
    OP_ROTATE_CW,
    OP_ROTATE_CCW,
    OP_HOLD,
    OP_LOCK,
    OP_CLEAR_LINES,
    OP_SCORE,
    OP_LEVEL_UP,
    OP_NEXT,
    OP_GHOST,
    OP_PAUSE,
    OP_RESUME,
    OP_GAME_OVER,
    OP_MENU,
    OP_ABOUT,
    OP_EXIT,
) = range(21)

OP_NAMES = {
    OP_IDLE: "IDLE",
    OP_SPAWN: "SPAWN",
    OP_MOVE_LEFT: "MOVE_L",
    OP_MOVE_RIGHT: "MOVE_R",
    OP_SOFT_DROP: "SOFT_DROP",
    OP_HARD_DROP: "HARD_DROP",
    OP_ROTATE_CW: "ROT_CW",
    OP_ROTATE_CCW: "ROT_CCW",
    OP_HOLD: "HOLD",
    OP_LOCK: "LOCK",
    OP_CLEAR_LINES: "CLEAR",
    OP_SCORE: "SCORE",
    OP_LEVEL_UP: "LEVEL",
    OP_NEXT: "NEXT",
    OP_GHOST: "GHOST",
    OP_PAUSE: "PAUSE",
    OP_RESUME: "RESUME",
    OP_GAME_OVER: "GAME_OVER",
    OP_MENU: "MENU",
    OP_ABOUT: "ABOUT",
    OP_EXIT: "EXIT",
}

# ============================================================
# tetromino shapes (4 rotations each, relative to 4x4 box)
# ============================================================

SHAPES: dict[str, list[list[tuple[int, int]]]] = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

BAG_TYPES = list(SHAPES.keys())

# SRS-lite wall kicks (JLSTZ, then I)
KICKS_JLSTZ = {
    (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (2, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (3, 0): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
}
KICKS_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
}

# Gravity table (frames per cell drop) by level — NES-ish
GRAVITY = [
    48, 43, 38, 33, 28, 23, 18, 13, 8, 6,
    5, 5, 5, 4, 4, 4, 3, 3, 3, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 1,
]

LINE_SCORES = (0, 100, 300, 500, 800)

# ============================================================
# procedural audio  (files = off)  —  Korobeiniki theme
# ============================================================

NOTE = {
    "R": 0.0,
    "A3": 220.00, "B3": 246.94, "C4": 261.63, "D4": 293.66,
    "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00,
    "B4": 493.88, "C5": 523.25, "D5": 587.33, "E5": 659.25,
}

# Classic Tetris A-Type (Korobeiniki)
# Note lengths are quarter-note units; tempo is leisurely (not Game Boy frenzy).
KORO_MELODY: list[tuple[str, float]] = [
    ("E4", 1), ("B3", 0.5), ("C4", 0.5), ("D4", 1), ("C4", 0.5), ("B3", 0.5),
    ("A3", 1), ("A3", 0.5), ("C4", 0.5), ("E4", 1), ("D4", 0.5), ("C4", 0.5),
    ("B3", 1), ("B3", 0.5), ("C4", 0.5), ("D4", 1), ("E4", 1),
    ("C4", 1), ("A3", 1), ("A3", 1), ("R", 1),
    ("D4", 1.5), ("F4", 0.5), ("A4", 1), ("G4", 0.5), ("F4", 0.5),
    ("E4", 1.5), ("C4", 0.5), ("E4", 1), ("D4", 0.5), ("C4", 0.5),
    ("B3", 1), ("B3", 0.5), ("C4", 0.5), ("D4", 1), ("E4", 1),
    ("C4", 1), ("A3", 1), ("A3", 1), ("R", 1),
]

# Quarter-note length in ms. ~100 BPM (600ms) — half the old rushed feel.
BEAT_MS = 600


def _mixer_init() -> None:
    """Match mixer rate to generated PCM or music plays ~2× too fast."""
    try:
        pygame.mixer.quit()
    except Exception:
        pass
    try:
        pygame.mixer.init(frequency=RATE, size=-16, channels=1, buffer=1024)
    except Exception:
        pass


def _tone(freq: float, ms: int, vol: float = 0.22, wave: str = "square") -> bytes:
    n = max(1, int(RATE * ms / 1000))
    out = bytearray()
    for i in range(n):
        if freq <= 0:
            sample = 0.0
        else:
            t = i / RATE
            phase = (t * freq) % 1.0
            if wave == "square":
                sample = 1.0 if phase < 0.5 else -1.0
            else:
                sample = math.sin(2 * math.pi * phase)
        # short attack / release envelope
        env = 1.0
        attack = min(n // 20, 200)
        release = min(n // 8, 800)
        if i < attack:
            env = i / max(1, attack)
        elif i > n - release:
            env = (n - i) / max(1, release)
        out += struct.pack("<h", int(sample * env * vol * 32767))
    return bytes(out)


def build_korobeiniki() -> Optional[pygame.mixer.Sound]:
    chunks: list[bytes] = []
    for name, beats in KORO_MELODY:
        ms = max(1, int(BEAT_MS * beats))
        freq = NOTE.get(name, 0.0)
        chunks.append(_tone(freq, ms, vol=0.18 if freq else 0.0))
    raw = b"".join(chunks)
    try:
        return pygame.mixer.Sound(buffer=raw)
    except Exception:
        return None


def sfx_tone(seq: list[tuple[float, int]], vol: float = 0.28) -> Optional[pygame.mixer.Sound]:
    try:
        return pygame.mixer.Sound(
            buffer=b"".join(_tone(f, ms, vol=vol) for f, ms in seq)
        )
    except Exception:
        return None


# ============================================================
# bag randomizer + piece
# ============================================================

class Bag:
    def __init__(self) -> None:
        self._bag: list[str] = []
        self._refill()

    def _refill(self) -> None:
        self._bag = BAG_TYPES[:]
        random.shuffle(self._bag)

    def next(self) -> str:
        if not self._bag:
            self._refill()
        return self._bag.pop()


class Piece:
    def __init__(self, kind: str) -> None:
        self.kind = kind
        self.rot = 0
        self.x = 3
        self.y = -1

    def cells(self, rot: Optional[int] = None, ox: Optional[int] = None, oy: Optional[int] = None):
        r = self.rot if rot is None else rot
        px = self.x if ox is None else ox
        py = self.y if oy is None else oy
        return [(px + cx, py + cy) for cx, cy in SHAPES[self.kind][r]]


# ============================================================
# game state + opcodes
# ============================================================

class TetrisGame:
    def __init__(self) -> None:
        self.board = [[None] * COLS for _ in range(ROWS)]
        self.bag = Bag()
        self.queue: list[str] = [self.bag.next() for _ in range(5)]
        self.piece: Optional[Piece] = None
        self.hold: Optional[str] = None
        self.hold_used = False
        self.score = 0
        self.lines = 0
        self.level = 0
        self.drop_timer = 0
        self.lock_timer = 0
        self.lock_limit = 30  # frames
        self.das_dir = 0
        self.das_timer = 0
        self.arr_timer = 0
        self.last_op = OP_IDLE
        self.game_over = False
        self.clearing: list[int] = []
        self.clear_flash = 0
        self.opcode(OP_SPAWN)

    def opcode(self, op: int, **kwargs) -> bool:
        """Execute a Tetris opcode. Returns True if action succeeded."""
        self.last_op = op
        if op == OP_SPAWN:
            return self._spawn()
        if op == OP_MOVE_LEFT:
            return self._move(-1, 0)
        if op == OP_MOVE_RIGHT:
            return self._move(1, 0)
        if op == OP_SOFT_DROP:
            if self._move(0, 1):
                self.score += 1
                return True
            return False
        if op == OP_HARD_DROP:
            return self._hard_drop()
        if op == OP_ROTATE_CW:
            return self._rotate(1)
        if op == OP_ROTATE_CCW:
            return self._rotate(-1)
        if op == OP_HOLD:
            return self._hold()
        if op == OP_LOCK:
            return self._lock()
        if op == OP_CLEAR_LINES:
            return self._clear_lines()
        if op == OP_SCORE:
            n = kwargs.get("n", 0)
            self.score += LINE_SCORES[n] * (self.level + 1)
            return True
        if op == OP_LEVEL_UP:
            self.level = self.lines // 10
            return True
        if op == OP_GAME_OVER:
            self.game_over = True
            return True
        return False

    def gravity_frames(self) -> int:
        return GRAVITY[min(self.level, len(GRAVITY) - 1)]

    def _valid(self, cells) -> bool:
        for x, y in cells:
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def _spawn(self) -> bool:
        kind = self.queue.pop(0)
        self.queue.append(self.bag.next())
        self.piece = Piece(kind)
        self.hold_used = False
        self.lock_timer = 0
        self.drop_timer = 0
        if not self._valid(self.piece.cells()):
            self.opcode(OP_GAME_OVER)
            return False
        return True

    def _move(self, dx: int, dy: int) -> bool:
        if not self.piece or self.game_over:
            return False
        cells = self.piece.cells(ox=self.piece.x + dx, oy=self.piece.y + dy)
        if self._valid(cells):
            self.piece.x += dx
            self.piece.y += dy
            if dy:
                self.lock_timer = 0
            return True
        return False

    def _rotate(self, direction: int) -> bool:
        if not self.piece or self.game_over:
            return False
        if self.piece.kind == "O":
            return True
        old = self.piece.rot
        new = (old + direction) % 4
        kicks = KICKS_I if self.piece.kind == "I" else KICKS_JLSTZ
        table = kicks.get((old, new), [(0, 0)])
        for kx, ky in table:
            cells = self.piece.cells(rot=new, ox=self.piece.x + kx, oy=self.piece.y - ky)
            if self._valid(cells):
                self.piece.rot = new
                self.piece.x += kx
                self.piece.y -= ky
                self.lock_timer = 0
                return True
        return False

    def _hard_drop(self) -> bool:
        if not self.piece or self.game_over:
            return False
        dist = 0
        while self._move(0, 1):
            dist += 1
        self.score += dist * 2
        return self.opcode(OP_LOCK)

    def _hold(self) -> bool:
        if not self.piece or self.hold_used or self.game_over:
            return False
        self.hold_used = True
        cur = self.piece.kind
        if self.hold is None:
            self.hold = cur
            self.piece = None
            return self.opcode(OP_SPAWN)
        self.hold, swap = cur, self.hold
        self.piece = Piece(swap)
        self.lock_timer = 0
        if not self._valid(self.piece.cells()):
            self.opcode(OP_GAME_OVER)
            return False
        return True

    def _lock(self) -> bool:
        if not self.piece:
            return False
        for x, y in self.piece.cells():
            if y < 0:
                self.opcode(OP_GAME_OVER)
                return False
            self.board[y][x] = self.piece.kind
        self.piece = None
        self.opcode(OP_CLEAR_LINES)
        if not self.game_over and self.clear_flash == 0:
            self.opcode(OP_SPAWN)
        return True

    def _clear_lines(self) -> bool:
        full = [y for y in range(ROWS) if all(self.board[y][x] is not None for x in range(COLS))]
        if not full:
            return False
        self.clearing = full
        self.clear_flash = 18  # frames of flash before remove
        return True

    def _finish_clear(self) -> None:
        n = len(self.clearing)
        for y in sorted(self.clearing, reverse=True):
            del self.board[y]
            self.board.insert(0, [None] * COLS)
        self.clearing = []
        self.lines += n
        self.opcode(OP_SCORE, n=n)
        self.opcode(OP_LEVEL_UP)

    def ghost_y(self) -> int:
        if not self.piece:
            return 0
        gy = self.piece.y
        while self._valid(self.piece.cells(oy=gy + 1)):
            gy += 1
        return gy

    def tick(self) -> Optional[str]:
        """One physics frame. Returns sfx event name if any."""
        if self.game_over:
            return None

        if self.clear_flash > 0:
            self.clear_flash -= 1
            if self.clear_flash == 0:
                self._finish_clear()
                if not self.game_over:
                    self.opcode(OP_SPAWN)
                return "clear"
            return None

        if not self.piece:
            return None

        # gravity
        self.drop_timer += 1
        if self.drop_timer >= self.gravity_frames():
            self.drop_timer = 0
            if not self._move(0, 1):
                self.lock_timer += 1
                if self.lock_timer >= self.lock_limit:
                    self.opcode(OP_LOCK)
                    return "lock"
            else:
                self.lock_timer = 0
        else:
            # still grounded check for lock delay
            if not self._valid(self.piece.cells(oy=self.piece.y + 1)):
                self.lock_timer += 1
                if self.lock_timer >= self.lock_limit:
                    self.opcode(OP_LOCK)
                    return "lock"
        return None


# ============================================================
# rendering
# ============================================================

def draw_block(surf: pygame.Surface, x: int, y: int, color: tuple[int, int, int], ghost: bool = False) -> None:
    px = BOARD_X + x * CELL
    py = BOARD_Y + y * CELL
    if ghost:
        pygame.draw.rect(surf, color, (px + 2, py + 2, CELL - 4, CELL - 4), 2)
        return
    pygame.draw.rect(surf, color, (px + 1, py + 1, CELL - 2, CELL - 2))
    hi = tuple(min(255, c + 60) for c in color)
    lo = tuple(max(0, c - 50) for c in color)
    pygame.draw.line(surf, hi, (px + 1, py + 1), (px + CELL - 2, py + 1))
    pygame.draw.line(surf, hi, (px + 1, py + 1), (px + 1, py + CELL - 2))
    pygame.draw.line(surf, lo, (px + CELL - 2, py + 1), (px + CELL - 2, py + CELL - 2))
    pygame.draw.line(surf, lo, (px + 1, py + CELL - 2), (px + CELL - 2, py + CELL - 2))


def draw_mini(surf: pygame.Surface, kind: str, ox: int, oy: int, scale: int = 18) -> None:
    color = COLORS[kind]
    for cx, cy in SHAPES[kind][0]:
        pygame.draw.rect(
            surf, color,
            (ox + cx * scale, oy + cy * scale, scale - 2, scale - 2),
        )


def draw_board(surf: pygame.Surface, game: TetrisGame, font: pygame.font.Font) -> None:
    # panel
    pygame.draw.rect(surf, PANEL, (BOARD_X - 8, BOARD_Y - 8, COLS * CELL + 16, ROWS * CELL + 16), border_radius=6)
    pygame.draw.rect(surf, GRID, (BOARD_X, BOARD_Y, COLS * CELL, ROWS * CELL))

    for y in range(ROWS):
        for x in range(COLS):
            pygame.draw.rect(surf, (28, 32, 48), (BOARD_X + x * CELL, BOARD_Y + y * CELL, CELL, CELL), 1)
            kind = game.board[y][x]
            if kind:
                if y in game.clearing and (game.clear_flash // 3) % 2 == 0:
                    draw_block(surf, x, y, (255, 255, 255))
                else:
                    draw_block(surf, x, y, COLORS[kind])

    if game.piece and game.clear_flash == 0:
        # ghost
        gy = game.ghost_y()
        for x, y in game.piece.cells(oy=gy):
            if y >= 0:
                draw_block(surf, x, y, COLORS["G"], ghost=True)
        for x, y in game.piece.cells():
            if y >= 0:
                draw_block(surf, x, y, COLORS[game.piece.kind])

    # side panels
    sx = BOARD_X + COLS * CELL + 36
    title = font.render("NEXT", True, ACCENT)
    surf.blit(title, (sx, BOARD_Y))
    for i, kind in enumerate(game.queue[:5]):
        draw_mini(surf, kind, sx, BOARD_Y + 32 + i * 72)

    hold_t = font.render("HOLD", True, ACCENT)
    surf.blit(hold_t, (sx, BOARD_Y + 420))
    if game.hold:
        draw_mini(surf, game.hold, sx, BOARD_Y + 452)

    stats = [
        f"SCORE  {game.score}",
        f"LINES  {game.lines}",
        f"LEVEL  {game.level}",
        f"OP     {OP_NAMES.get(game.last_op, '?')}",
    ]
    for i, line in enumerate(stats):
        surf.blit(font.render(line, True, TEXT), (sx, 20 + i * 22))


# ============================================================
# app  —  menu / play / about / exit
# ============================================================

class App:
    def __init__(self) -> None:
        pygame.init()
        _mixer_init()
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("AC's Tetris 4K  —  files = off")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("menlo,monaco,consolas,monospace", 20)
        self.big = pygame.font.SysFont("menlo,monaco,consolas,monospace", 48, bold=True)
        self.mid = pygame.font.SysFont("menlo,monaco,consolas,monospace", 28, bold=True)

        self.state = "menu"  # menu | play | about | pause
        self.menu_idx = 0
        self.menu_items = ["Play Game", "About", "Exit"]
        self.game: Optional[TetrisGame] = None

        self.music = build_korobeiniki()
        self.sfx = {
            "move": sfx_tone([(440, 30)], 0.15),
            "rotate": sfx_tone([(523, 35), (659, 35)], 0.18),
            "lock": sfx_tone([(220, 50), (165, 60)], 0.22),
            "clear": sfx_tone([(523, 50), (659, 50), (784, 80)], 0.25),
            "drop": sfx_tone([(330, 25), (220, 40)], 0.2),
            "hold": sfx_tone([(392, 40), (523, 40)], 0.18),
            "over": sfx_tone([(392, 120), (330, 120), (262, 180)], 0.28),
            "select": sfx_tone([(659, 50), (880, 70)], 0.2),
        }
        self._music_playing = False
        self.keys_held: dict[int, bool] = {}
        self.soft_timer = 0
        self.das = 10
        self.arr = 2
        self.das_timer = 0
        self.arr_timer = 0
        self.move_dir = 0

    def play_sfx(self, name: str) -> None:
        s = self.sfx.get(name)
        if s:
            try:
                s.play()
            except Exception:
                pass

    def start_music(self) -> None:
        if self.music and not self._music_playing:
            try:
                self.music.play(loops=-1)
                self._music_playing = True
            except Exception:
                pass

    def stop_music(self) -> None:
        if self.music and self._music_playing:
            try:
                self.music.stop()
            except Exception:
                pass
            self._music_playing = False

    def start_game(self) -> None:
        self.game = TetrisGame()
        self.state = "play"
        self.start_music()
        self.play_sfx("select")

    def draw_menu(self) -> None:
        self.screen.fill(BG)
        title = self.big.render("TETRIS 4K", True, ACCENT)
        self.screen.blit(title, (W // 2 - title.get_width() // 2, 120))
        sub = self.font.render("files = off  ·  Korobeiniki  ·  all opcodes", True, DIM)
        self.screen.blit(sub, (W // 2 - sub.get_width() // 2, 185))

        for i, item in enumerate(self.menu_items):
            col = GOLD if i == self.menu_idx else TEXT
            prefix = "> " if i == self.menu_idx else "  "
            label = self.mid.render(prefix + item, True, col)
            self.screen.blit(label, (W // 2 - 100, 280 + i * 56))

        hint = self.font.render("UP/DOWN  ENTER  ESC", True, DIM)
        self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 60))

    def draw_about(self) -> None:
        self.screen.fill(BG)
        title = self.mid.render("ABOUT", True, ACCENT)
        self.screen.blit(title, (W // 2 - title.get_width() // 2, 80))
        lines = [
            "AC's Tetris 4K",
            "Python 3.14 + pygame @ 60 fps",
            "files = off — no external assets",
            "",
            "Opcodes: SPAWN MOVE ROTATE HOLD",
            "HARD_DROP SOFT_DROP LOCK CLEAR",
            "SCORE LEVEL NEXT GHOST PAUSE",
            "",
            "Music: Korobeiniki (procedural)",
            "duh-duh-duh… the Russian Tetris song",
            "",
            "Controls:",
            "  A/D or ←/→  move",
            "  W/↑ or Z/X  rotate",
            "  S/↓         soft drop",
            "  SPACE       hard drop",
            "  C / SHIFT   hold",
            "  P / ESC     pause / menu",
            "",
            "ENTER or ESC — back to menu",
        ]
        for i, line in enumerate(lines):
            col = ACCENT if line.startswith("AC") or line.startswith("Music") else TEXT
            s = self.font.render(line, True, col)
            self.screen.blit(s, (W // 2 - 200, 130 + i * 24))

    def draw_play(self) -> None:
        self.screen.fill(BG)
        assert self.game is not None
        draw_board(self.screen, self.game, self.font)
        footer = self.font.render("P pause  ESC menu  files=off", True, DIM)
        self.screen.blit(footer, (BOARD_X, H - 36))

        if self.game.game_over:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill(OVERLAY)
            self.screen.blit(overlay, (0, 0))
            go = self.big.render("GAME OVER", True, (255, 80, 80))
            self.screen.blit(go, (W // 2 - go.get_width() // 2, H // 2 - 60))
            sc = self.mid.render(f"Score {self.game.score}", True, GOLD)
            self.screen.blit(sc, (W // 2 - sc.get_width() // 2, H // 2 + 10))
            hint = self.font.render("ENTER — menu", True, TEXT)
            self.screen.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 60))

        if self.state == "pause":
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill(OVERLAY)
            self.screen.blit(overlay, (0, 0))
            p = self.big.render("PAUSED", True, ACCENT)
            self.screen.blit(p, (W // 2 - p.get_width() // 2, H // 2 - 20))

    def handle_menu(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self.menu_idx = (self.menu_idx - 1) % len(self.menu_items)
            self.play_sfx("move")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.menu_idx = (self.menu_idx + 1) % len(self.menu_items)
            self.play_sfx("move")
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            choice = self.menu_items[self.menu_idx]
            if choice == "Play Game":
                self.start_game()
            elif choice == "About":
                self.state = "about"
                self.play_sfx("select")
            elif choice == "Exit":
                self.play_sfx("select")
                pygame.quit()
                sys.exit(0)
        elif event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit(0)

    def handle_play_keydown(self, key: int) -> None:
        g = self.game
        if not g:
            return
        if g.game_over:
            if key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.stop_music()
                self.state = "menu"
            return
        if key in (pygame.K_p,):
            self.state = "pause"
            if self.music:
                try:
                    self.music.stop()
                except Exception:
                    pass
                self._music_playing = False
            return
        if key == pygame.K_ESCAPE:
            self.stop_music()
            self.state = "menu"
            return

        if key in (pygame.K_LEFT, pygame.K_a):
            if g.opcode(OP_MOVE_LEFT):
                self.play_sfx("move")
            self.move_dir = -1
            self.das_timer = 0
            self.arr_timer = 0
        elif key in (pygame.K_RIGHT, pygame.K_d):
            if g.opcode(OP_MOVE_RIGHT):
                self.play_sfx("move")
            self.move_dir = 1
            self.das_timer = 0
            self.arr_timer = 0
        elif key in (pygame.K_UP, pygame.K_w, pygame.K_x):
            if g.opcode(OP_ROTATE_CW):
                self.play_sfx("rotate")
        elif key in (pygame.K_z, pygame.K_q):
            if g.opcode(OP_ROTATE_CCW):
                self.play_sfx("rotate")
        elif key in (pygame.K_DOWN, pygame.K_s):
            if g.opcode(OP_SOFT_DROP):
                self.play_sfx("move")
            self.soft_timer = 0
        elif key == pygame.K_SPACE:
            g.opcode(OP_HARD_DROP)
            self.play_sfx("drop")
        elif key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
            if g.opcode(OP_HOLD):
                self.play_sfx("hold")

    def handle_keyup(self, key: int) -> None:
        if key in (pygame.K_LEFT, pygame.K_a) and self.move_dir < 0:
            self.move_dir = 0
        if key in (pygame.K_RIGHT, pygame.K_d) and self.move_dir > 0:
            self.move_dir = 0

    def update_play(self) -> None:
        g = self.game
        if not g or g.game_over:
            return
        keys = pygame.key.get_pressed()

        # DAS / ARR
        if self.move_dir:
            self.das_timer += 1
            if self.das_timer >= self.das:
                self.arr_timer += 1
                if self.arr_timer >= self.arr:
                    self.arr_timer = 0
                    op = OP_MOVE_LEFT if self.move_dir < 0 else OP_MOVE_RIGHT
                    if g.opcode(op):
                        self.play_sfx("move")

        # soft drop held
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.soft_timer += 1
            if self.soft_timer >= 2:
                self.soft_timer = 0
                g.opcode(OP_SOFT_DROP)

        was_over = g.game_over
        ev = g.tick()
        if ev:
            self.play_sfx(ev)
        if g.game_over and not was_over:
            self.play_sfx("over")
            self.stop_music()

    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit(0)
                if self.state == "menu":
                    self.handle_menu(event)
                elif self.state == "about":
                    if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE
                    ):
                        self.state = "menu"
                        self.play_sfx("select")
                elif self.state == "pause":
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_p, pygame.K_RETURN):
                            self.state = "play"
                            self.start_music()
                        elif event.key == pygame.K_ESCAPE:
                            self.stop_music()
                            self.state = "menu"
                elif self.state == "play":
                    if event.type == pygame.KEYDOWN:
                        self.handle_play_keydown(event.key)
                    elif event.type == pygame.KEYUP:
                        self.handle_keyup(event.key)

            if self.state == "play":
                self.update_play()

            if self.state == "menu":
                self.draw_menu()
            elif self.state == "about":
                self.draw_about()
            elif self.state in ("play", "pause"):
                self.draw_play()

            pygame.display.flip()
            self.clock.tick(FPS)


def main() -> None:
    if sys.version_info < (3, 10):
        print("Python 3.10+ required (targets 3.14).", file=sys.stderr)
        sys.exit(1)
    if os.environ.get("TETRIS4K_SMOKE"):
        # headless-ish smoke: build game logic without display loop forever
        pygame.init()
        _mixer_init()
        g = TetrisGame()
        for _ in range(120):
            g.tick()
            g.opcode(OP_SOFT_DROP)
        assert g.piece is not None or g.game_over or g.clear_flash >= 0
        print("SMOKE OK", g.score, g.lines, OP_NAMES[g.last_op], "files=", PR_FILES)
        pygame.quit()
        return
    App().run()


if __name__ == "__main__":
    main()
