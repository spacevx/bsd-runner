import json
from pathlib import Path

configFile: str = "config.json"


def load() -> None:
    path = Path(configFile)
    if not path.exists():
        return
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return

    from keybindings import keyBindings
    if "keybindings" in data:
        kb = data["keybindings"]
        for attr in ("jump", "slide", "restart"):
            if attr in kb:
                setattr(keyBindings, attr, kb[attr])

    import settings
    if "bSoundEnabled" in data:
        settings.bSoundEnabled = data["bSoundEnabled"]

    if "levelCompleted" in data:
        settings.levelCompleted = {int(k): v for k, v in data["levelCompleted"].items()}
    if "levelUnlocked" in data:
        settings.levelUnlocked = {int(k): v for k, v in data["levelUnlocked"].items()}
        settings.levelUnlocked[1] = True

    if "bLevel1Completed" in data and data["bLevel1Completed"]:
        settings.levelCompleted[1] = True
    if "bLevel2Completed" in data and data["bLevel2Completed"]:
        settings.levelCompleted[2] = True
    if "bLevel2Unlocked" in data and data["bLevel2Unlocked"]:
        settings.levelUnlocked[2] = True


def save() -> None:
    from keybindings import keyBindings
    import settings

    data = {
        "keybindings": {
            "jump": keyBindings.jump,
            "slide": keyBindings.slide,
            "restart": keyBindings.restart,
        },
        "bSoundEnabled": settings.bSoundEnabled,
        "levelCompleted": {str(k): v for k, v in settings.levelCompleted.items()},
        "levelUnlocked": {str(k): v for k, v in settings.levelUnlocked.items()},
    }
    with open(configFile, "w") as f:
        json.dump(data, f, indent=2)
