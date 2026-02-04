from typing import Callable

import pygame
from pygame import Surface
from pygame.event import Event
from pygame.sprite import Group


import flags
from settings import GameState, ScreenSize, width, height, obstacleSpawnEvent
from entities import (
    Player, Chaser, Obstacle, FallingCage, Ceiling,
    TileSet, GroundTilemap, CeilingTileSet, CeilingTilemap
)
from paths import assetsPath, screensPath

from .hud import HUD
from .spawner import ObstacleSpawner
from .collision import CollisionSystem

tilesPath = assetsPath / "tiles" / "ground"
ceilingTilesPath = assetsPath / "tiles" / "ceiling"
songsPath = assetsPath / "songs"

class GameScreen:
    baseW: int = 1920
    baseH: int = 1080
    scrollSpeedConst: float = 400.0
    groundRatio: float = 1.0

    # Initialise l'écran de jeu, les entités, collisions et audio
    def __init__(self, setStateCallback: Callable[[GameState], None]) -> None:
        self.setState = setStateCallback
        self.screenSize: ScreenSize = (width, height)
        self.scale = min(width / self.baseW, height / self.baseH) 

        Obstacle.clearCache()
        self._loadBackground()

        self.scrollX: float = 0.0
        self.scrollSpeed = self.scrollSpeedConst
        self.groundY = int(height * self.groundRatio)

        # Callbacks pour les sons du saut et du glissement
        self.localPlayer = Player(self._s(320), self.groundY, onJump=self._playJumpSound, onSlide=self._playSlideSound)
        self.chaser: Chaser | None = None if flags.bDisableChaser else Chaser(self._s(-200), self.groundY)

        self.allSprites: Group[pygame.sprite.Sprite] = pygame.sprite.Group()
        self.allSprites.add(self.localPlayer)
        if self.chaser:
            self.allSprites.add(self.chaser)

        self.obstacles: Group[Obstacle] = pygame.sprite.Group()
        self.ceiling = Ceiling(self.screenSize[0], self.screenSize[1])
        self.fallingCages: Group[FallingCage] = pygame.sprite.Group()

        self.score: int = 0
        self.bGameOver: bool = False
        self.invincibleTimer: float = 0.0
        self.invincibleDuration: float = 1.0

        self.bPlayerTrapped: bool = False
        self.trappedTimer: float = 0.0
        self.trappedDuration: float = 4.0
        self.trappingCage: FallingCage | None = None

        self._initTilemap()
        self._initCeilingTilemap()

        self.hud = HUD(self.screenSize)
        self.spawner = ObstacleSpawner(self.screenSize, self.groundY, self.scrollSpeed)
        self.collisionSystem = CollisionSystem(self.screenSize)
        
        # audio placeholders
        self.bgMusic = None
        self.cageSound = None        # Sons pour les actions du joueur        self.jumpSound = None
        self.slideSound = None
        self.slideDelayTimer = 0.0
        self.slideDelay = 0.0  # délai avant de jouer le son du slide
        self.soundTimer = 0.0
        self.soundDuration = 5.0
        self.soundActive = False
        self._loadCageSound()
        self._loadJumpSound()
        self._loadSlideSound()
        self.startAudio()


    def _loadAudio(self) -> None:
        # Charge la musique de fond
        try:
            bgm_path = songsPath / "The Good Fight (just intro).ogg"
            self.bgMusic = pygame.mixer.Sound(str(bgm_path))
        except (pygame.error, FileNotFoundError) as e:
            print(f"Erreur lors du chargement du son: {e}")
            self.bgMusic = None

    def _loadCageSound(self) -> None:
        # Charge le son de la cage depuis le fichier metal3.ogg
        try:
            cage_path = songsPath / "metal3.ogg"
            self.cageSound = pygame.mixer.Sound(str(cage_path))
        except (pygame.error, FileNotFoundError) as e:
            print(f"Erreur lors du chargement du son de la cage: {e}")
            self.cageSound = None

    def _loadJumpSound(self) -> None:
        # Charge le son du saut depuis le fichier jump.ogg
        try:
            jump_path = songsPath / "jump.ogg"
            self.jumpSound = pygame.mixer.Sound(str(jump_path))
        except (pygame.error, FileNotFoundError) as e:
            print(f"Erreur lors du chargement du son du saut: {e}")
            self.jumpSound = None

    def _loadSlideSound(self) -> None:
        # Charge le son du glissement depuis le fichier cartoon-slide.ogg
        try:
            slide_path = songsPath / "cartoon-slide.ogg"
            self.slideSound = pygame.mixer.Sound(str(slide_path))
        except (pygame.error, FileNotFoundError) as e:
            print(f"Erreur lors du chargement du son du glissement: {e}")
            self.slideSound = None

    def _playJumpSound(self) -> None:
        # Joue le son du saut
        if self.jumpSound:
            self.jumpSound.play()

    def _playSlideSound(self) -> None:
        #joue le son de slide 
        if self.slideSound:
            self.slideSound.play()


    def startAudio(self) -> None:
        # charge le son si besoin et le joue; active le timer de répétition
        if self.bgMusic is None:
            self._loadAudio()
        if self.bgMusic:
            self.bgMusic.play(-1)  # -1 pour jouer en boucle infinie
            self.soundTimer = 0.0
            self.soundActive = True

    def stopAudio(self) -> None:
        # arrête la musique et désactive la logique de répétition
        if self.bgMusic:
            try:
                self.bgMusic.stop()
            except Exception:
                pass
        self.soundActive = False

    def _s(self, val: int) -> int:
        return max(1, int(val * self.scale))

    def _loadBackground(self) -> None:
        path = screensPath / "background.png"
        try:
            original = pygame.image.load(str(path)).convert()
            self.background = pygame.transform.scale(original, self.screenSize)
        except (pygame.error, FileNotFoundError):
            self.background = self._createFallbackBackground()
        self.bgWidth = self.background.get_width()

    def _createFallbackBackground(self) -> Surface:
        w, h = self.screenSize
        surface = pygame.Surface((w, h))

        for y in range(int(h * self.groundRatio)):
            t = y / (h * self.groundRatio)
            r = int(100 + 35 * t)
            g = int(160 + 46 * t)
            b = int(220 + 35 * (1 - t))
            pygame.draw.line(surface, (r, g, b), (0, y), (w, y))

        return surface.convert()

    def _initTilemap(self) -> None:
        w, h = self.screenSize
        groundH = h - self.groundY
        self.tileset = TileSet(tilesPath)
        self.groundTilemap = GroundTilemap(self.tileset, w, self.groundY, groundH)

    def _initCeilingTilemap(self) -> None:
        w = self.screenSize[0]
        self.ceilingTileset = CeilingTileSet(ceilingTilesPath)
        self.ceilingTilemap = CeilingTilemap(self.ceilingTileset, w, self.ceiling.height)

    def onResize(self, newSize: ScreenSize) -> None:
        self.screenSize = newSize
        self.scale = min(newSize[0] / self.baseW, newSize[1] / self.baseH)
        self._loadBackground()
        self.groundY = int(newSize[1] * self.groundRatio)

        self.localPlayer.setGroundY(self.groundY)
        if self.chaser:
            self.chaser.setGroundY(self.groundY)

        groundH = newSize[1] - self.groundY
        self.groundTilemap.on_resize(newSize[0], self.groundY, groundH)
        self.ceiling.onResize(newSize[0])
        self.ceilingTilemap.on_resize(newSize[0], self.ceiling.height)

        self.hud.onResize(newSize)
        self.spawner.onResize(newSize, self.groundY)
        self.collisionSystem.onResize(newSize)

    def reset(self) -> None:
        Obstacle.clearCache()
        FallingCage.clearCache()
        self.groundY = int(self.screenSize[1] * self.groundRatio)

        # Callbacks pour les sons du saut et du glissement au reset
        self.localPlayer = Player(self._s(320), self.groundY, onJump=self._playJumpSound, onSlide=self._playSlideSound)
        self.chaser = None if flags.bDisableChaser else Chaser(self._s(-200), self.groundY)

        self.allSprites.empty()
        self.allSprites.add(self.localPlayer)
        if self.chaser:
            self.allSprites.add(self.chaser)

        self.obstacles.empty()
        self.fallingCages.empty()
        self._initCeilingTilemap()

        self.scrollX = 0.0
        self.score = 0
        self.bGameOver = False
        self.invincibleTimer = 0.0

        self.bPlayerTrapped = False
        self.trappedTimer = 0.0
        self.trappingCage = None

        self.spawner.reset()
        self.startAudio()

    def handleEvent(self, event: Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.bGameOver:
                self.reset()
            elif not self.bGameOver:
                self.localPlayer.handleInput(event)

        self.spawner.handleEvent(event, self.obstacles, self.bGameOver)

    def update(self, dt: float) -> None:
        if self.bGameOver:
            return

        if self.bPlayerTrapped:
            self._updateTrapped(dt)
            return

        scrollDelta = self.scrollSpeed * dt
        self.scrollX += scrollDelta
        if self.scrollX >= self.bgWidth:
            self.scrollX -= self.bgWidth

        self.groundTilemap.update(scrollDelta)
        cageXs = self.ceilingTilemap.update(scrollDelta)
        for cx in cageXs:
            self.spawner.spawnCageAt(cx, self.ceiling.height, self.fallingCages)

        self.score += int(self.scrollSpeed * dt * 0.1)

        if self.invincibleTimer > 0:
            self.invincibleTimer -= dt

        self.localPlayer.update(dt)
        if self.localPlayer.velocity.x != 0:
            self.localPlayer.rect.x += int(self.localPlayer.velocity.x * dt)
        if self.chaser:
            self.chaser.setTarget(self.localPlayer.rect.centerx)
            self.chaser.update(dt, self.fallingCages)
        self.obstacles.update(dt)

        playerX = self.localPlayer.rect.centerx
        for cage in self.fallingCages:
            cage.update(dt, playerX)

        self._handleCollisions()
        
        

    def _updateTrapped(self, dt: float) -> None:
        self.trappedTimer -= dt
        self.localPlayer.update(dt)
        if self.trappingCage:
            self.trappingCage.update(dt)
            self.localPlayer.rect.centerx = self.trappingCage.rect.centerx
            self.localPlayer.rect.bottom = self.groundY
        if self.trappedTimer <= 0:
            self.bGameOver = True
            pygame.time.set_timer(obstacleSpawnEvent, 0)

    def _handleCollisions(self) -> None:
        bInvincible = self.invincibleTimer > 0
        result = self.collisionSystem.check(
            self.localPlayer, self.chaser, self.obstacles, self.fallingCages, bInvincible
        )

        if result.bHitObstacle:
            self.invincibleTimer = self.invincibleDuration
            if self.chaser:
                self.chaser.onPlayerHit()
            # arrêter la musique si le joueur est touché
            try:
                self.stopAudio()
            except Exception:
                pass

        if result.bHitCage and result.trappingCage:
            self.bPlayerTrapped = True
            self.trappedTimer = self.trappedDuration
            self.trappingCage = result.trappingCage
            self.trappingCage.trapPlayer(self.localPlayer.rect.centerx)
            self.localPlayer.trap()
            pygame.time.set_timer(obstacleSpawnEvent, 0)
            try:
                self.stopAudio()
                # Joue le son de la cage quand le joueur est attrapé
                if self.cageSound:
                    self.cageSound.play()
            except Exception:
                pass

        if result.bCaught:
            self.bGameOver = True
            pygame.time.set_timer(obstacleSpawnEvent, 0)
            try:
                self.stopAudio()
            except Exception:
                pass

    def draw(self, screen: Surface) -> None:
        self._drawScrollingBackground(screen)
        self.groundTilemap.draw(screen)
        self.obstacles.draw(screen)

        if self.bPlayerTrapped and self.trappingCage:
            screen.blit(self.localPlayer.image, self.localPlayer.rect)
        else:
            if not (self.invincibleTimer > 0 and int(self.invincibleTimer * 10) % 2 == 0):
                screen.blit(self.localPlayer.image, self.localPlayer.rect)

        if self.chaser:
            screen.blit(self.chaser.image, self.chaser.rect)
        self.ceilingTilemap.draw(screen)

        for cage in self.fallingCages:
            cage.draw(screen)

        self.hud.draw(screen, self.score, self.bGameOver)

    def _drawScrollingBackground(self, screen: Surface) -> None:
        x1 = -int(self.scrollX)
        x2 = x1 + self.bgWidth
        screen.blit(self.background, (x1, 0))
        screen.blit(self.background, (x2, 0))