from dataclasses import dataclass
from pathlib import Path

from paths import assetsPath, screensPath


@dataclass(frozen=True)
class LevelConfig:
    levelId: int
    name: str
    gravity: float
    jumpForce: float
    bDoubleJump: bool
    doubleJumpForce: float
    bSlideEnabled: bool
    coyoteTime: float
    jumpBuffer: float
    scrollSpeed: float
    bSpeedGrowth: bool
    speedGrowth: float
    maxSpeed: float
    obstacleMinDelay: float
    obstacleMaxDelay: float
    bFallingCages: bool
    finaleScore: int
    laneDodgeScore: int
    maxHits: int
    slowdownDuration: float
    slowdownMult: float
    obstacleDir: Path
    backgroundPath: Path
    chaserFramesPath: Path
    bHasCeilingTiles: bool
    bHasGroundTiles: bool
    bLaserEnabled: bool
    laserCooldown: float
    laserRange: float
    bHasChaser: bool
    bGeometricObstacles: bool


level1Config = LevelConfig(
    levelId=1,
    name="NIVEAU 1",
    gravity=1100.0,
    jumpForce=-650.0,
    bDoubleJump=False,
    doubleJumpForce=0.0,
    bSlideEnabled=True,
    coyoteTime=0.0,
    jumpBuffer=0.0,
    scrollSpeed=400.0,
    bSpeedGrowth=False,
    speedGrowth=0.0,
    maxSpeed=400.0,
    obstacleMinDelay=2.5,
    obstacleMaxDelay=5.0,
    bFallingCages=True,
    finaleScore=3000,
    laneDodgeScore=100,
    maxHits=3,
    slowdownDuration=0.8,
    slowdownMult=0.4,
    obstacleDir=assetsPath / "lanes",
    backgroundPath=screensPath / "background.png",
    chaserFramesPath=assetsPath / "chaser" / "running" / "frames",
    bHasCeilingTiles=True,
    bHasGroundTiles=True,
    bLaserEnabled=False,
    laserCooldown=0.0,
    laserRange=0.0,
    bHasChaser=True,
    bGeometricObstacles=False,
)

level2Config = LevelConfig(
    levelId=2,
    name="NIVEAU 2",
    gravity=2200.0,
    jumpForce=-860.0,
    bDoubleJump=True,
    doubleJumpForce=-780.0,
    bSlideEnabled=False,
    coyoteTime=0.09,
    jumpBuffer=0.11,
    scrollSpeed=420.0,
    bSpeedGrowth=True,
    speedGrowth=6.0,
    maxSpeed=900.0,
    obstacleMinDelay=0.7,
    obstacleMaxDelay=1.7,
    bFallingCages=False,
    finaleScore=5000,
    laneDodgeScore=100,
    maxHits=3,
    slowdownDuration=1.15,
    slowdownMult=0.68,
    obstacleDir=assetsPath / "lanes",
    backgroundPath=assetsPath / "level2" / "background.png",
    chaserFramesPath=assetsPath / "chaser" / "running" / "frames",
    bHasCeilingTiles=False,
    bHasGroundTiles=True,
    bLaserEnabled=False,
    laserCooldown=0.0,
    laserRange=0.0,
    bHasChaser=True,
    bGeometricObstacles=False,
)

level3Config = LevelConfig(
    levelId=3,
    name="NIVEAU 3",
    gravity=1800.0,
    jumpForce=-700.0,
    bDoubleJump=False,
    doubleJumpForce=0.0,
    bSlideEnabled=True,
    coyoteTime=0.08,
    jumpBuffer=0.1,
    scrollSpeed=600.0,
    bSpeedGrowth=False,
    speedGrowth=0.0,
    maxSpeed=600.0,
    obstacleMinDelay=0.7,
    obstacleMaxDelay=1.7,
    bFallingCages=False,
    finaleScore=2000,
    laneDodgeScore=50,
    maxHits=3,
    slowdownDuration=0.0,
    slowdownMult=1.0,
    obstacleDir=assetsPath / "geometric",
    backgroundPath=assetsPath / "level3" / "background.png",
    chaserFramesPath=assetsPath / "chaser" / "running" / "frames",
    bHasCeilingTiles=False,
    bHasGroundTiles=True,
    bLaserEnabled=True,
    laserCooldown=0.2,
    laserRange=800.0,
    bHasChaser=False,
    bGeometricObstacles=True,
)

levelConfigs: dict[int, LevelConfig] = {1: level1Config, 2: level2Config, 3: level3Config}
