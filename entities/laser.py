import math
import random

import pygame
from pygame import Surface
from pygame.math import Vector2


class LaserParticle:
    __slots__ = ("pos", "vel", "life", "maxLife", "radius")

    def __init__(self, pos: Vector2, vel: Vector2, life: float, radius: float) -> None:
        self.pos = pos.copy()
        self.vel = vel
        self.life = life
        self.maxLife = life
        self.radius = radius

    def update(self, dt: float) -> bool:
        self.pos += self.vel * dt
        self.vel *= 0.92
        self.life -= dt
        return self.life > 0


class LaserBeam:
    duration: float = 0.18
    particleCount: int = 24
    segmentCount: int = 14
    waveAmplitude: float = 4.5
    waveFrequency: float = 38.0
    impactParticleCount: int = 8

    def __init__(self, startX: int, startY: int, endX: int, endY: int) -> None:
        self.start = Vector2(startX, startY)
        self.end = Vector2(endX, endY)
        self.timer = self.duration
        self.bActive = True
        self.age: float = 0.0
        self.beamLength = self.start.distance_to(self.end)
        self.bHitSomething = endX < startX + 780

        self.particles: list[LaserParticle] = []
        self.impactParticles: list[LaserParticle] = []
        self._spawnBeamParticles()
        if self.bHitSomething:
            self._spawnImpactParticles()

    def _spawnBeamParticles(self) -> None:
        direction = (self.end - self.start)
        if direction.length_squared() < 1:
            return
        direction = direction.normalize()
        perp = Vector2(-direction.y, direction.x)

        for _ in range(self.particleCount):
            t = random.random()
            basePos = self.start.lerp(self.end, t)
            offset = perp * random.uniform(-6, 6)
            pos = basePos + offset

            speed = random.uniform(15, 60)
            angle = random.uniform(0, math.tau)
            vel = Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            vel += perp * random.uniform(-20, 20)

            life = random.uniform(0.08, 0.16)
            radius = random.uniform(1.2, 3.0)
            self.particles.append(LaserParticle(pos, vel, life, radius))

    def _spawnImpactParticles(self) -> None:
        for _ in range(self.impactParticleCount):
            speed = random.uniform(60, 200)
            angle = random.uniform(math.pi * 0.3, math.pi * 1.7)
            vel = Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            spreadPos = self.end + Vector2(random.uniform(-4, 4), random.uniform(-4, 4))
            life = random.uniform(0.1, 0.2)
            radius = random.uniform(1.5, 4.0)
            self.impactParticles.append(LaserParticle(spreadPos, vel, life, radius))

    def update(self, dt: float) -> None:
        self.timer -= dt
        self.age += dt
        if self.timer <= 0:
            self.bActive = False

        self.particles = [p for p in self.particles if p.update(dt)]
        self.impactParticles = [p for p in self.impactParticles if p.update(dt)]

    @property
    def bDone(self) -> bool:
        return not self.bActive and not self.particles and not self.impactParticles

    def _beamColor(self, t: float, layer: int) -> tuple[int, int, int, int]:
        pulse = 0.5 + 0.5 * math.sin(self.age * 60.0)
        alphaBase = int(255 * t)

        if layer == 0:
            r = int(255 * (0.7 + 0.3 * pulse))
            return (r, 20, 0, min(50, alphaBase // 4))
        elif layer == 1:
            g = int(40 + 40 * pulse)
            return (255, g, 10, min(100, alphaBase // 3))
        elif layer == 2:
            g = int(80 + 50 * pulse)
            b = int(30 + 30 * pulse)
            return (255, g, b, min(150, alphaBase // 2))
        else:
            g = int(180 + 60 * pulse)
            b = int(150 + 80 * pulse)
            return (255, g, b, alphaBase)

    def _buildSegmentPoints(self, layer: int) -> list[tuple[int, int]]:
        return [(int(self.start.x), int(self.start.y)), (int(self.end.x), int(self.end.y))]

    def draw(self, screen: Surface) -> None:
        if not self.bActive and not self.particles and not self.impactParticles:
            return

        t = max(self.timer / self.duration, 0.0)

        if self.bActive and t > 0.01:
            layerWidths = [22, 14, 9, 4]
            for layer in range(4):
                color = self._beamColor(t, layer)
                points = self._buildSegmentPoints(layer)
                if len(points) >= 2:
                    pygame.draw.lines(screen, color, False, points, layerWidths[layer])

            if self.bHitSomething:
                self._drawImpactFlash(screen, t)

            self._drawMuzzleFlash(screen, t)

        self._drawParticles(screen, self.particles, t, bImpact=False)
        self._drawParticles(screen, self.impactParticles, t, bImpact=True)

    def _drawMuzzleFlash(self, screen: Surface, t: float) -> None:
        pulse = 0.6 + 0.4 * math.sin(self.age * 80.0)
        radius = int(12 * t * pulse)
        if radius < 2:
            return
        alpha = int(180 * t * pulse)
        flashSurf = Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(flashSurf, (255, 160, 80, alpha), (radius, radius), radius)
        screen.blit(flashSurf, (int(self.start.x) - radius, int(self.start.y) - radius))

        coreR = max(2, int(radius * 0.5))
        coreSurf = Surface((coreR * 2, coreR * 2), pygame.SRCALPHA)
        pygame.draw.circle(coreSurf, (255, 240, 220, min(255, int(alpha * 1.3))), (coreR, coreR), coreR)
        screen.blit(coreSurf, (int(self.start.x) - coreR, int(self.start.y) - coreR))

    def _drawImpactFlash(self, screen: Surface, t: float) -> None:
        pulse = 0.5 + 0.5 * math.sin(self.age * 70.0)
        baseRadius = int(18 * t * pulse)
        if baseRadius < 2:
            return

        outerR = baseRadius + 4
        outerAlpha = int(100 * t * pulse)
        outerSurf = Surface((outerR * 2, outerR * 2), pygame.SRCALPHA)
        pygame.draw.circle(outerSurf, (255, 80, 20, outerAlpha), (outerR, outerR), outerR)
        screen.blit(outerSurf, (int(self.end.x) - outerR, int(self.end.y) - outerR))

        innerAlpha = int(200 * t * pulse)
        flashSurf = Surface((baseRadius * 2, baseRadius * 2), pygame.SRCALPHA)
        pygame.draw.circle(flashSurf, (255, 200, 120, innerAlpha), (baseRadius, baseRadius), baseRadius)
        screen.blit(flashSurf, (int(self.end.x) - baseRadius, int(self.end.y) - baseRadius))

        coreR = max(2, int(baseRadius * 0.4))
        coreSurf = Surface((coreR * 2, coreR * 2), pygame.SRCALPHA)
        pygame.draw.circle(coreSurf, (255, 255, 240, min(255, int(innerAlpha * 1.4))), (coreR, coreR), coreR)
        screen.blit(coreSurf, (int(self.end.x) - coreR, int(self.end.y) - coreR))

    def _drawParticles(self, screen: Surface, particles: list[LaserParticle],
                       t: float, *, bImpact: bool) -> None:
        for p in particles:
            frac = p.life / p.maxLife
            alpha = int(255 * frac * max(t, 0.3))
            r = max(1, int(p.radius * frac))

            if bImpact:
                g = int(120 + 100 * frac)
                b = int(40 + 60 * frac)
            else:
                g = int(80 + 80 * frac)
                b = int(20 + 40 * frac)

            if r <= 1:
                screen.set_at((int(p.pos.x), int(p.pos.y)), (255, g, b, alpha))
            else:
                pSurf = Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(pSurf, (255, g, b, alpha), (r, r), r)
                screen.blit(pSurf, (int(p.pos.x) - r, int(p.pos.y) - r))
