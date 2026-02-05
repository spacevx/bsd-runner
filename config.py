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
    if "bLevel2Unlocked" in data:
        settings.bLevel2Unlocked = data["bLevel2Unlocked"]


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
        "bLevel2Unlocked": settings.bLevel2Unlocked,
    }
    with open(configFile, "w") as f:
        json.dump(data, f, indent=2)
