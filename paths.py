import sys
from pathlib import Path
from typing import Final

def getBasePath() -> Path:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(getattr(sys, '_MEIPASS'))
    return Path(__file__).parent


basePath: Final[Path] = getBasePath()
assetsPath: Final[Path] = basePath / "assets"
screensPath: Final[Path] = basePath / "screens"