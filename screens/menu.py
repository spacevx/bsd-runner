import math
from typing import Callable

import pygame
import pygame_gui
from pygame import Surface
from pygame.event import Event
from pygame.font import Font
from pygame_gui import UIManager
from pygame_gui.elements import UIButton
from pygame_gui.core import ObjectID

from settings import WIDTH, HEIGHT, GameState, Color, ScreenSize


class MainMenu:
    BASE_W: int = 1920
    BASE_H: int = 1080

    def __init__(self, set_state_callback: Callable[[GameState], None]) -> None:
        self.set_state: Callable[[GameState], None] = set_state_callback
        self.screen_size: ScreenSize = (WIDTH, HEIGHT)
        self.scale: float = min(WIDTH / self.BASE_W, HEIGHT / self.BASE_H)

        self.manager: UIManager = UIManager(self.screen_size, theme_path=None)
        self._setup_theme()

        self.bg_cache: Surface | None = None
        self.vignette_cache: Surface | None = None
        self.scanlines_cache: Surface | None = None
        self.octagon_glow_cache: Surface | None = None
        self.fence_cache: tuple[Surface, Surface] | None = None

        self._build_caches()

        self.start_btn: UIButton | None = None
        self.options_btn: UIButton | None = None
        self.quit_btn: UIButton | None = None
        self._create_buttons()

        self.title_font: Font = pygame.font.Font(None, self._s(160))

        self.time: float = 0.0
        self.spotlight_flicker: float = 1.0
        self.title_pulse: float = 0.0

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _setup_theme(self) -> None:
        bw, bh = self._s(400), self._s(70)
        self.manager.get_theme().load_theme({
            "button": {
                "colours": {
                    "normal_bg": "#8B0000",
                    "hovered_bg": "#B22222",
                    "active_bg": "#DC143C",
                    "normal_border": "#4A4A4A",
                    "hovered_border": "#C0C0C0",
                    "active_border": "#FFD700",
                    "normal_text": "#FFFFFF",
                    "hovered_text": "#FFFFFF",
                    "active_text": "#FFFFFF"
                },
                "font": {
                    "name": "noto_sans",
                    "size": str(self._s(28)),
                    "bold": "1"
                },
                "misc": {
                    "shape": "rounded_rectangle",
                    "shape_corner_radius": "4",
                    "border_width": "3"
                }
            }
        })

    def _get_button_rects(self) -> list[pygame.Rect]:
        w, h = self._s(400), self._s(70)
        cx = (self.screen_size[0] - w) // 2
        base_y = int(self.screen_size[1] * 0.58)
        gap = self._s(90)
        return [
            pygame.Rect(cx, base_y, w, h),
            pygame.Rect(cx, base_y + gap, w, h),
            pygame.Rect(cx, base_y + gap * 2, w, h),
        ]

    def _create_buttons(self) -> None:
        rects = self._get_button_rects()
        self.start_btn = UIButton(
            relative_rect=rects[0], text="COMMENCER LE JEU",
            manager=self.manager, object_id=ObjectID(object_id="#start_btn")
        )
        self.options_btn = UIButton(
            relative_rect=rects[1], text="OPTIONS",
            manager=self.manager, object_id=ObjectID(object_id="#options_btn")
        )
        self.quit_btn = UIButton(
            relative_rect=rects[2], text="QUITTER",
            manager=self.manager, object_id=ObjectID(object_id="#quit_btn")
        )

    def _update_button_positions(self) -> None:
        rects = self._get_button_rects()
        for btn, rect in zip([self.start_btn, self.options_btn, self.quit_btn], rects):
            if btn:
                btn.set_relative_position((rect.x, rect.y))
                btn.set_dimensions((rect.width, rect.height))

    def _build_caches(self) -> None:
        w, h = self.screen_size
        self.bg_cache = self._create_gradient_bg(w, h)
        self.vignette_cache = self._create_vignette(w, h)
        self.scanlines_cache = self._create_scanlines(w, h)
        self.octagon_glow_cache = self._create_octagon_glow(w, h)
        self.fence_cache = self._create_fence_panels(w, h)

    def _create_gradient_bg(self, w: int, h: int) -> Surface:
        surf = pygame.Surface((w, h))
        for y in range(h):
            t = y / h
            r = int(5 + 35 * t * t)
            g = int(2 + 5 * t)
            b = int(5 + 8 * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (w, y))
        return surf.convert()

    def _create_vignette(self, w: int, h: int) -> Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        max_dist = math.hypot(cx, cy)
        for ring in range(0, int(max_dist), 4):
            t = ring / max_dist
            alpha = int(180 * (t ** 2.5))
            alpha = min(255, alpha)
            if alpha > 0:
                pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), int(max_dist - ring), 4)
        return surf.convert_alpha()

    def _create_scanlines(self, w: int, h: int) -> Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(0, h, 3):
            pygame.draw.line(surf, (0, 0, 0, 25), (0, y), (w, y))
        return surf.convert_alpha()

    def _create_octagon_glow(self, w: int, h: int) -> Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, int(h * 0.48)
        radius = self._s(280)

        for glow_r in range(radius + self._s(60), radius, -2):
            alpha = int(15 * (1 - (glow_r - radius) / self._s(60)))
            pts = [(cx + glow_r * math.cos(math.pi / 8 + i * math.pi / 4),
                    cy + glow_r * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
            pygame.draw.polygon(surf, (139, 0, 0, alpha), pts, self._s(3))

        pts_outer = [(cx + radius * math.cos(math.pi / 8 + i * math.pi / 4),
                      cy + radius * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
        pygame.draw.polygon(surf, (80, 80, 90), pts_outer, self._s(4))

        inner_r = radius - self._s(25)
        pts_inner = [(cx + inner_r * math.cos(math.pi / 8 + i * math.pi / 4),
                      cy + inner_r * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
        pygame.draw.polygon(surf, (60, 60, 70), pts_inner, self._s(2))

        inner_r2 = radius - self._s(50)
        pts_inner2 = [(cx + inner_r2 * math.cos(math.pi / 8 + i * math.pi / 4),
                       cy + inner_r2 * math.sin(math.pi / 8 + i * math.pi / 4)) for i in range(8)]
        pygame.draw.polygon(surf, (45, 45, 55), pts_inner2, self._s(1))

        for i in range(8):
            angle = math.pi / 8 + i * math.pi / 4
            x1, y1 = cx + inner_r2 * math.cos(angle), cy + inner_r2 * math.sin(angle)
            x2, y2 = cx + radius * math.cos(angle), cy + radius * math.sin(angle)
            pygame.draw.line(surf, (50, 50, 60), (x1, y1), (x2, y2), self._s(2))

        return surf.convert_alpha()

    def _create_fence_panels(self, w: int, h: int) -> tuple[Surface, Surface]:
        panel_w = self._s(120)
        left = pygame.Surface((panel_w, h), pygame.SRCALPHA)
        right = pygame.Surface((panel_w, h), pygame.SRCALPHA)

        spacing = self._s(18)
        wire_color = (50, 50, 60, 180)
        highlight = (70, 70, 80, 100)

        for surf, flip in [(left, False), (right, True)]:
            for y in range(-spacing, h + spacing, spacing):
                for x in range(-spacing, panel_w + spacing, spacing):
                    x1, y1 = x, y
                    x2, y2 = x + spacing, y + spacing
                    pygame.draw.line(surf, wire_color, (x1, y1), (x2, y2), 1)
                    pygame.draw.line(surf, wire_color, (x2, y1), (x1, y2), 1)

            for x in range(0, panel_w, spacing):
                for y in range(0, h, spacing):
                    pygame.draw.circle(surf, highlight, (x, y), 2)

            fade_w = panel_w
            for i in range(fade_w):
                alpha = int(255 * (i / fade_w) if flip else 255 * (1 - i / fade_w))
                pygame.draw.line(surf, (0, 0, 0, alpha), (i, 0), (i, h))

        return left.convert_alpha(), right.convert_alpha()

    def _draw_spotlight(self, surf: Surface) -> None:
        w, h = self.screen_size
        cx = w // 2
        spot_h = int(h * 0.5)
        spot_surf = pygame.Surface((w, spot_h), pygame.SRCALPHA)

        intensity = 0.7 + 0.3 * self.spotlight_flicker

        for y in range(spot_h):
            t = y / spot_h
            width = int(self._s(50) + t * self._s(400))
            alpha = int(35 * intensity * (1 - t * 0.7))
            if alpha > 0 and width > 0:
                rect = pygame.Rect(cx - width // 2, y, width, 1)
                pygame.draw.rect(spot_surf, (255, 250, 240, alpha), rect)

        surf.blit(spot_surf, (0, 0), special_flags=pygame.BLEND_ADD)

    def _draw_title(self, surf: Surface) -> None:
        w, h = self.screen_size
        cx, ty = w // 2, int(h * 0.18)
        text = "MMA"
        pulse = 0.9 + 0.1 * math.sin(self.title_pulse)

        for offset in range(self._s(20), 0, -2):
            alpha = int(80 * (1 - offset / self._s(20)) * pulse)
            glow_surf = self.title_font.render(text, True, (139, 0, 0))
            glow_surf.set_alpha(alpha)
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
                rect = glow_surf.get_rect(center=(cx + dx, ty + dy))
                surf.blit(glow_surf, rect)

        shadow = self.title_font.render(text, True, (20, 0, 0))
        shadow_rect = shadow.get_rect(center=(cx + self._s(5), ty + self._s(5)))
        surf.blit(shadow, shadow_rect)

        base = self.title_font.render(text, True, (180, 180, 190))
        base_rect = base.get_rect(center=(cx, ty))
        surf.blit(base, base_rect)

        gradient_surf = pygame.Surface(base.get_size(), pygame.SRCALPHA)
        tw, th = base.get_size()
        for y in range(th):
            t = y / th
            if t < 0.5:
                r = int(220 + 35 * (1 - t * 2))
                g = int(220 + 35 * (1 - t * 2))
                b = int(230 + 25 * (1 - t * 2))
            else:
                r = int(150 + 70 * (t - 0.5) * 2)
                g = int(150 + 70 * (t - 0.5) * 2)
                b = int(160 + 70 * (t - 0.5) * 2)
            pygame.draw.line(gradient_surf, (r, g, b, 255), (0, y), (tw, y))

        mask = pygame.mask.from_surface(base)
        mask_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
        gradient_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(gradient_surf, base_rect)

        highlight = pygame.Surface((tw, th // 3), pygame.SRCALPHA)
        for y in range(th // 3):
            alpha = int(60 * (1 - y / (th // 3)))
            pygame.draw.line(highlight, (255, 255, 255, alpha), (0, y), (tw, y))
        highlight_masked = pygame.Surface((tw, th), pygame.SRCALPHA)
        highlight_masked.blit(highlight, (0, 0))
        highlight_masked.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(highlight_masked, base_rect, special_flags=pygame.BLEND_ADD)

    def on_resize(self, new_size: ScreenSize) -> None:
        self.screen_size = new_size
        self.scale = min(new_size[0] / self.BASE_W, new_size[1] / self.BASE_H)
        self.manager.set_window_resolution(new_size)
        self._setup_theme()
        self._build_caches()
        self._update_button_positions()
        self.title_font = pygame.font.Font(None, self._s(160))

    def handle_event(self, event: Event) -> None:
        self.manager.process_events(event)

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.start_btn:
                self.set_state(GameState.GAME)
            elif event.ui_element == self.options_btn:
                self.set_state(GameState.OPTIONS)
            elif event.ui_element == self.quit_btn:
                self.set_state(GameState.QUIT)

    def update(self, dt: float) -> None:
        self.time += dt
        self.title_pulse += dt * 3
        self.spotlight_flicker = 0.85 + 0.15 * math.sin(self.time * 8) + 0.1 * math.sin(self.time * 13)
        self.manager.update(dt)

    def draw(self, screen: Surface) -> None:
        w, h = self.screen_size

        if self.bg_cache:
            screen.blit(self.bg_cache, (0, 0))
        if self.octagon_glow_cache:
            screen.blit(self.octagon_glow_cache, (0, 0))
        self._draw_spotlight(screen)

        if self.fence_cache:
            screen.blit(self.fence_cache[0], (0, 0))
            screen.blit(self.fence_cache[1], (w - self.fence_cache[1].get_width(), 0))

        if self.vignette_cache:
            screen.blit(self.vignette_cache, (0, 0))
        if self.scanlines_cache:
            screen.blit(self.scanlines_cache, (0, 0))

        self._draw_title(screen)

        self.manager.draw_ui(screen)
