from dataclasses import dataclass

import pygame
from pygame.sprite import Group

from entities import Player, PlayerState, Chaser, Obstacle, ObstacleType, FallingCage, CageState


@dataclass
class CollisionResult:
    bHitObstacle: bool = False
    bHitCage: bool = False
    bCaught: bool = False


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

        if obstacle.obstacleType == ObstacleType.LOW and player.state == PlayerState.JUMPING:
            if playerHitbox.bottom < obstacleHitbox.top + self._s(20):
                return False

        if obstacle.obstacleType == ObstacleType.HIGH and player.state == PlayerState.SLIDING:
            if playerHitbox.top > obstacleHitbox.bottom - self._s(15):
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
            if playerHitbox.top > cageHitbox.bottom - self._s(30):
                return False

        return True

    def check(self, player: Player, chaser: Chaser, obstacles: Group[Obstacle],
              cages: Group[FallingCage], bInvincible: bool) -> CollisionResult:
        result = CollisionResult()

        if bInvincible:
            if chaser.hasCaughtPlayer(player.getHitbox()):
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
            hitCages[0].kill()

        if chaser.hasCaughtPlayer(player.getHitbox()):
            result.bCaught = True

        return result
