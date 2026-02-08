# BSD Runner

A runner game on the MMA fighter Benoit Saint Denis

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat&logo=python)
![Pygame](https://img.shields.io/badge/Pygame--CE-2.5+-green?style=flat&logo=python)
![mypy](https://img.shields.io/badge/mypy-strict-blue?style=flat)

## Levels

**Level 1** - You're getting chased by Jon Jones, one of Benoit Saint Denis nemesis. You have to dodge the differents obstacles by jumping or sliding. There is also cages that falls from the ceiling

**Level 2** - Same as level 1 but instead of sliding you can double jump. The speed is also increasing over time (from 420 to 900)

**Level 3** - Geometry Dash like level, there is geometric obstacles and you have to dodge them or destroy them with your laser

## Features

- Gamepad support (Xbox, PlayStation) but only in gameplay (not in the menus)
- Discord Rich Presence
- You can change your keybindings in the options
- A CI/CD pipeline is present to build & release the game, you just have to change the version in `pyproject.toml`

## Installation

### From release

Download the latest release from [GitHub Releases](https://github.com/spacevx/bsd-runner/releases) and extract `MMA.zip`

### From source

```bash
git clone https://github.com/spacevx/bsd-runner.git
cd bsd-runner
pip install -r requirements.txt
python main.py
```

**Requirements**: Python 3.11+

### Dependencies

| Package | What its for |
|---------|---------|
| pygame-ce | Game engine |
| Pillow | Used for GIF Tool |
| pytablericons | Icons library |
| pypresence | Discord Rich Presence |

## Commands

```bash
# Run the game
python main.py

# Type checking
mypy .

# Build Windows executable
pyinstaller build.spec
```

## Flags

| Flag | What it does |
|------|-------------|
| `--disableChaser` | Run the game without the chaser enemy |
| `--unlockAllLevels` | Unlock all levels |

Usage: `python main.py --disableChaser --unlockAllLevels` (you can combine them)

To add a new flag, go to `flags.py`, add a new `bool` variable (prefixed with `b`), then add a `parser.add_argument("--yourFlag", action="store_true")` and assign it from `parsed`. Then you can use `flags.bYourFlag` anywhere in the code.

## Options

- You can change your controls (only for keyboard players)
- You can also toggle the sound on/off

## Easter Eggs

**Levels 1 & 2**: Do the combo JUMP, JUMP + SLIDE (hold both together), SLIDE and it will activate a random visual effect, the two existing ones are inverted colors and mirrored screen.

**Level 3**: If you press SPACE 5+ times in less than 10 seconds, the geometric obstacles will transform into rotating heads.

## Architecture

```
mma/
  main.py
  game.py              # Manages the differents screens
  settings.py          # Constants & differents vars
  levels.py            # Level config, you can config each level here
  config.py            # JSON config (settings, keybindings, progress)
  discord.py           # Discord Rich Presence
  entities/
    player.py           # Our Player
    chaser.py           # The chaser, (only available in level 1)
    animation.py        # Class used to animated frames
    tilemap.py          # Ground/ceiling tilemap (ground is not really useful, only the ceiling one is really used for the cages)
    obstacle/           # Obstacles logic, there is BaseObstacle and all Obstacle are child of BaseObstacle
    input/              # Input manager, keybindings, joystick
  screens/
    menu.py             # Start Menu
    level_select.py     # Level selector, to choose a level to play
    options.py          # Options
    game/
      screen.py         # Render logic
      hud.py            # All the hud in game (score, life, keys)
      collision.py      # Collision logic
      spawner.py        # Logic for spawning obstacles (when, where, can we)?
    ui/                 # UI Lib, all our components are reusable
  assets/               # All our assets
  tools/                # Useful tools
```

## CI/CD

- **mypy.yml**: Type checking on every push/PR (just like a tsconfig.json)
- **release.yml**: Auto builds Windows executable and creates a release when the version in `pyproject.toml` changes

## Code Style
- camelCase for variables, `b` prefix for booleans (`bGameOver`, `bDoubleJump`)
- Typed code
- All UI strings are located in `strings.py`
- The player is referenced as the `local player` so localPlayer = Player