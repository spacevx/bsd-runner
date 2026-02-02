import pygame
from pygame import Surface, Rect
from pygame.sprite import Sprite

from settings import Color


class Chaser(Sprite):
    BASE_SPEED: float = 150.0
    SPEED_BOOST_ON_HIT: float = 50.0
    APPROACH_ON_HIT: int = 80
    FOLLOW_OFFSET: int = 150
    WIDTH: int = 140
    HEIGHT: int = 95

    def __init__(self, x: int, ground_y: int) -> None:
        super().__init__()

        self.image: Surface = self._create_image()
        self.rect: Rect = self.image.get_rect(midbottom=(x, ground_y))

        self.ground_y = ground_y
        self.pos_x = float(x)
        self.target_x = x
        self.speed = self.BASE_SPEED

    def _create_image(self) -> Surface:
        surface: Surface = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)

        body_color: Color = (80, 50, 30)
        horn_color: Color = (200, 180, 150)

        pygame.draw.ellipse(surface, body_color, (10, 25, 110, 55))
        pygame.draw.circle(surface, body_color, (110, 45), 28)
        pygame.draw.polygon(surface, horn_color, [(120, 25), (140, 8), (130, 30)])
        pygame.draw.polygon(surface, horn_color, [(120, 65), (140, 82), (130, 60)])
        pygame.draw.circle(surface, (0, 0, 0), (124, 40), 5)
        pygame.draw.circle(surface, (255, 0, 0), (124, 40), 3)
        pygame.draw.rect(surface, body_color, (16, 75, 12, 20))
        pygame.draw.rect(surface, body_color, (40, 75, 12, 20))
        pygame.draw.rect(surface, body_color, (70, 75, 12, 20))
        pygame.draw.rect(surface, body_color, (94, 75, 12, 20))
        pygame.draw.ellipse(surface, body_color, (0, 35, 25, 15))

        return surface

    def set_ground_y(self, ground_y: int) -> None:
        self.ground_y = ground_y
        self.rect.bottom = ground_y

    def set_target(self, player_x: int) -> None:
        self.target_x = player_x - self.FOLLOW_OFFSET

    def on_player_hit(self) -> None:
        self.speed += self.SPEED_BOOST_ON_HIT
        self.pos_x += self.APPROACH_ON_HIT

    def has_caught_player(self, player_rect: Rect) -> bool:
        return self.rect.colliderect(player_rect)

    def update(self, dt: float) -> None:
        if (diff := self.target_x - self.pos_x) > 0:
            self.pos_x += min(self.speed * dt, diff)
        elif diff < 0:
            self.pos_x -= min(self.speed * 0.5 * dt, -diff)

        self.pos_x = min(self.pos_x, self.target_x + self.FOLLOW_OFFSET - 50)
        self.rect.midbottom = (int(self.pos_x), self.ground_y)
