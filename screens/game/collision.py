from dataclasses import dataclass

import pygame
from pygame.sprite import Group

from entities import Player, PlayerState, Chaser, Obstacle, FallingCage, CageState


@dataclass
class CollisionResult:
    bHitObstacle: bool = False
    bHitCage: bool = False
    bCaught: bool = False
    trappingCage: FallingCage | None = None


class CollisionSystem:
    baseW: int = 1920
    baseH: int = 1080

    def __init__(self, screenSize: tuple[int, int]) -> None:
        self.scale = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def onResize(self, screenSize: tuple[int, int]) -> None:
        self.scale = min(screenSize[0] / self.baseW, screenSize[1] / self.baseH)

    def _obstacleCallback(self, player: Player, obstacle: Obstacle) -> bool:
        playerHitbox = player.getHitbox()
        obstacleHitbox = obstacle.get_hitbox()

        if not playerHitbox.colliderect(obstacleHitbox):
            return False

        if player.state == PlayerState.JUMPING:
            if playerHitbox.bottom < obstacleHitbox.top + self._s(15):
                return False

        return True

    def _cageCallback(self, player: Player, cage: FallingCage) -> bool:
        if cage.state not in (CageState.FALLING, CageState.GROUNDED):
            return False

        playerHitbox = player.getHitbox()
        cageHitbox = cage.get_hitbox()

        if not playerHitbox.colliderect(cageHitbox):
            return False

        if player.state == PlayerState.SLIDING:
            if playerHitbox.top > cageHitbox.bottom - self._s(150):
                return False

        return True

    def check(self, player: Player, chaser: Chaser | None, obstacles: Group[Obstacle],
              cages: Group[FallingCage], bInvincible: bool) -> CollisionResult:
        result = CollisionResult()

        if bInvincible:
            if chaser and chaser.hasCaughtPlayer(player.getHitbox()):
                result.bCaught = True
            return result

        hitObstacles: list[Obstacle] = pygame.sprite.spritecollide(
            player, obstacles, dokill=False, collided=self._obstacleCallback
        )

        if hitObstacles:
            result.bHitObstacle = True
            hitObstacles[0].kill()

        hitCages: list[FallingCage] = pygame.sprite.spritecollide(
            player, cages, dokill=False, collided=self._cageCallback
        )

        if hitCages:
            result.bHitCage = True
            result.trappingCage = hitCages[0]

        if chaser and chaser.hasCaughtPlayer(player.getHitbox()):
            result.bCaught = True

        return result
