# Advanced Snake Game

A feature-rich implementation of the classic Snake game built with Python and Pygame. This enhanced version includes advanced mechanics, stunning visual effects, sound effects, and a persistent leaderboard with player initials.

## Features

### Core Gameplay
- Classic Snake mechanics with modern enhancements
- 600×600 pixel window with 30×30 grid (20px cells)
- Smooth movement with collision detection
- Score tracking and display

### Advanced Mechanics
- **Score-based Snake Colors**: Snake changes color based on score tiers
- **Moving Food**: Some food items drift around the board
- **Special Foods**:
  - Normal food (+1 score)
  - Golden food (+3 score, special sound)
  - Rotten food (-1 score, shrinks snake)
- **Progressive Obstacles**: Obstacles spawn as you progress
- **Speed Scaling**: Game speed increases with each food eaten
- **Bounded Grid**: Snake dies on wall/obstacle collision (no wrapping)

### Audio & Visual
- **Sound Effects**: 
  - Eat sound for normal food
  - Special chime for golden food
  - Rotten buzz for bad food
  - Game over sound
- **Stunning Visual Effects**:
  - **Animated Gradient Background**: Smooth color-shifting background (blue → purple → pink)
  - **Snake Head with Personality**: 
    - Distinct head with white eyes and black pupils
    - Animated red forked tongue that flicks in and out
    - Head rotates based on movement direction
  - **Glowing Trail Effect**: Snake leaves a beautiful fading trail behind it
  - **Glowing Food**: 
    - Normal food: Pulsing green glow
    - Golden food: Bright yellow glow effect
    - Rotten food: Dark flickering effect
  - **Color-coded Snake**: Changes color based on score tiers
  - **Semi-transparent Game Over Overlay**: Elegant game over screen
  - **Real-time Score and Speed Display**

### Leaderboard
- **Player Initials Input**: Enter your 3-letter initials when you achieve a high score
- **Persistent Top 5 Scores**: Saved locally with initials and scores
- **Automatic Score Saving**: Scores are saved when you qualify for the leaderboard
- **Enhanced Display**: Shows initials and scores in a clean format

## Requirements

- Python 3.7 or higher
- Pygame 2.5.0 or higher

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## How to Run

```bash
python3 snake_pygame.py
```

## Controls

### Movement
- **Arrow Keys** or **WASD** to move the snake
- Snake cannot make 180° turns (prevents accidental self-collision)

### Game Controls
- **Space**: Pause/Resume game
- **R**: Restart game (when game over)
- **ESC**: Quit game

### High Score Input
- **Letters A-Z**: Enter your initials (3 letters max)
- **Backspace**: Delete last character
- **Enter**: Save score and restart game

## Game Mechanics

### Scoring System
- **Normal Food**: +1 point
- **Golden Food**: +3 points (rare spawn)
- **Rotten Food**: -1 point, shrinks snake by 1 segment

### Snake Color Tiers
The snake changes color based on your score:
- **0-4 points**: Green (#22c55e)
- **5-9 points**: Blue (#3b82f6)
- **10-19 points**: Purple (#a855f7)
- **20-34 points**: Orange (#f59e0b)
- **35-49 points**: Red (#ef4444)
- **50+ points**: Yellow (#eab308)

### Speed Progression
- Base speed: 8 FPS
- Speed increases by 0.6 FPS per food eaten
- Maximum speed: 22 FPS

### Obstacles
- Obstacles spawn every 3 foods eaten
- Maximum of 40 obstacles
- Obstacles never block food access completely
- Snake dies on obstacle collision

### Moving Food
- 30% chance for food to be moving
- Moving food drifts every 6 game ticks
- Food only moves to valid empty cells

## File Structure

```
snake-game/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── snake_pygame.py       # Main game code
└── leaderboard.json      # Persistent leaderboard (auto-created)
```

## Technical Details

### Configuration
The game features can be toggled in the `FEATURES` dictionary at the top of `snake_pygame.py`:
- `score_tier_colors`: Enable color-changing snake
- `moving_food`: Enable drifting food
- `special_food`: Enable golden/rotten food
- `progressive_obstacles`: Enable obstacle spawning
- `bounded_grid`: Enable wall collision
- `speed_scales_with_eats`: Enable speed progression
- `sound_effects`: Enable audio feedback
- `leaderboard`: Enable persistent scoring

### Game Tuning
Various game parameters can be adjusted in the `GAME_TUNING` dictionary:
- Grid cell size, food movement frequency
- Special food spawn rates
- Speed progression settings
- Score tier thresholds and colors
- Leaderboard size

## Troubleshooting

### Sound Issues
If you experience sound problems:
- The game will continue to work without sound
- Sound effects are generated programmatically
- Check your system's audio settings

### Performance Issues
- The game is optimized for 60 FPS
- If experiencing lag, try reducing the maximum speed in `GAME_TUNING`
- Close other applications to free up system resources

### Leaderboard Issues
- The leaderboard file (`leaderboard.json`) is created automatically
- If corrupted, delete the file and restart the game
- Leaderboard is stored in the same directory as the game

## Development

The game is built using object-oriented design with the main `SnakeGame` class handling all game logic. Key components:

- **Food System**: Handles different food types and movement
- **Snake Management**: Movement, growth, and collision detection with visual effects
- **Obstacle System**: Progressive obstacle spawning with pathfinding
- **Audio System**: Programmatically generated sound effects
- **Visual Effects System**: Animated backgrounds, glowing effects, and trail rendering
- **Leaderboard**: JSON-based persistent storage with initials support
- **Input System**: Handles movement, pause, and initials input

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the game!

## Contributors

This project was developed by:

- **Daudi Kirabo Makumbi Mawejje** - 189657
- **Aditya More** - 193384
- **Namara Joshua** – 192582
- **Agolor Blessing** – 223251
- **Ahmed Hussain** - 193285

---

Enjoy playing the Advanced Snake Game! 🐍
