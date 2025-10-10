# Snake Game Documentation

## Overview
This is an advanced Snake game built with Pygame featuring multiple food types, obstacles, sound effects, leaderboard, and visual enhancements. The game includes animated backgrounds, glowing effects, and progressive difficulty.

## File Structure
```
snake_pygame.py          # Main game file
leaderboard.json         # High scores storage
requirements.txt         # Python dependencies
README.md               # Project information
```

## Code Architecture

### 1. Imports and Dependencies
```python
import pygame          # Main game engine for graphics, sound, and input handling
import random          # For generating random positions and food types
import json           # For saving/loading leaderboard data
import os             # For file system operations (checking if files exist)
import sys            # For system operations (exiting the program)
import math           # For mathematical calculations (sin, cos for animations)
from enum import Enum # For creating enumerated constants (food types)
from typing import List, Tuple, Set, Optional, Dict, Any  # Type hints for better code documentation
from collections import deque  # For efficient snake body management (appendleft/pop operations)
```

### 2. Configuration System

#### FEATURES Dictionary
Controls which game features are enabled/disabled:
- `score_tier_colors`: Snake changes color based on score level
- `moving_food`: Food can move around the board
- `special_food`: Enable golden and rotten food types
- `progressive_obstacles`: Obstacles appear as game progresses
- `bounded_grid`: Snake dies when hitting walls (no wrapping)
- `speed_scales_with_eats`: Game speed increases with each food eaten
- `sound_effects`: Play sound effects for actions
- `leaderboard`: Save and display high scores

#### GAME_TUNING Dictionary
Contains all game balance parameters:
- **Grid settings**: `grid_cell` (20px), `leaderboard_size` (5)
- **Food behavior**: `food_move_every_n_ticks` (6), `special_spawn_chance` (0.22), `rotten_ratio_within_special` (0.35)
- **Snake settings**: `min_snake_len` (1)
- **Obstacle settings**: `obstacle_every_n_foods` (3), `max_obstacles` (40)
- **Speed progression**: `speed_base` (4), `speed_step_per_food` (0.3), `speed_max` (15)
- **Visual progression**: `score_tiers` and `tier_colors` for color changes

### 3. Constants and Enums

#### Game Constants
- `WINDOW_SIZE`: 600x600 pixel game window
- `GRID_SIZE`: 30x30 grid (calculated from window size)
- `FPS`: Target frames per second (120)

#### Color Definitions
- Basic colors: `BLACK`, `WHITE`, `GRAY`, `DARK_GRAY`
- Game colors: `RED`, `GREEN`, `BLUE`, `PURPLE`, `ORANGE`, `YELLOW`, `GOLD`, `BROWN`
- Accent colors: `PINK`, `CYAN`, `MAGENTA`, `LIGHT_BLUE`

#### FoodType Enum
```python
class FoodType(Enum):
    NORMAL = "normal"    # Regular food: +1 point, +1 length
    GOLDEN = "golden"    # Special food: +3 points, +1 length
    ROTTEN = "rotten"    # Bad food: -1 point, -1 length (min 1)
```

#### Direction Vectors
```python
DIRECTIONS = {
    "UP": (0, -1),       # Move up (decrease y)
    "DOWN": (0, 1),      # Move down (increase y)
    "LEFT": (-1, 0),     # Move left (decrease x)
    "RIGHT": (1, 0)      # Move right (increase x)
}
```

### 4. Food Class

#### Purpose
Represents food items on the game board with position, type, movement capability, and color.

#### Methods
- `__init__(pos, food_type, is_moving)`: Initialize food item
- `_get_color()`: Determine visual color based on food type

#### Attributes
- `pos`: Grid position (x, y)
- `type`: Food type enum
- `is_moving`: Whether food can move around
- `color`: RGB color tuple for rendering

### 5. SnakeGame Class

#### Purpose
Main game class that manages the entire Snake game, handling game state, rendering, input, sound, and game logic.

#### Key Attributes
- **Display**: `screen`, `clock`, `font`, `small_font`, `initials_font`
- **Game state**: `snake`, `direction`, `next_direction`, `score`, `food_eaten`, `tick_count`
- **Game objects**: `food`, `obstacles`, `concurrent_foods`
- **Visual effects**: `background_phase`, `tongue_out`, `tongue_timer`, `trail_surfaces`
- **Sound**: `sounds` dictionary
- **Leaderboard**: `leaderboard_file`, `leaderboard`
- **UI state**: `waiting_for_initials`, `player_initials`

#### Core Methods

##### Initialization and Setup
- `__init__()`: Initialize pygame, create display, load assets, reset game state
- `_load_sounds()`: Load or create sound effects programmatically
- `_generate_tone(frequency, duration, sample_rate)`: Generate sine wave tones for sounds

##### Leaderboard Management
- `_load_leaderboard()`: Load high scores from JSON file with format migration
- `_save_leaderboard()`: Save current leaderboard to JSON file
- `_add_to_leaderboard(score, initials)`: Add new score and maintain top scores list
- `reset_leaderboard()`: Clear all scores (called with 'L' key)

##### Game State Management
- `reset()`: Reset game to initial state (new game/restart)
- `spawn_food()`: Spawn new food at random empty position
- `_spawn_rotten_with_normal()`: Spawn both rotten and normal food simultaneously
- `_spawn_concurrent_food()`: Spawn bonus foods when rotten food is eaten

##### Obstacle Management
- `spawn_obstacle()`: Spawn obstacle at valid position (respects max count)
- `_is_food_accessible(new_obstacle)`: Use BFS to ensure food remains reachable

##### Game Logic
- `move_snake()`: Move snake one step, handle collisions, food consumption, growth
- `_eat_food()`: Handle main food consumption with score/speed changes
- `_eat_concurrent_food(food)`: Handle bonus food consumption
- `update_food()`: Update position of moving food items

##### Visual Effects
- `get_snake_color(score)`: Get snake color based on score tier
- `_draw_animated_background()`: Draw animated gradient background
- `_draw_snake_head(head_pos, direction, color)`: Draw detailed snake head with eyes/tongue
- `_draw_glowing_food(food)`: Draw food with glowing effect
- `_update_trail_effect()`: Update snake trail effects

##### Input Handling
- `handle_events()`: Process pygame events (keyboard, window close)
- `run()`: Main game loop

##### Drawing and Rendering
- `draw()`: Main drawing method that renders all game elements
- `_draw_game_over()`: Draw game over overlay with leaderboard
- `_draw_leaderboard()`: Draw leaderboard on game over screen
- `_draw_initials_input()`: Handle initials input display

### 6. Game Flow

#### Initialization
1. Initialize pygame modules
2. Create game window and fonts
3. Load sound effects
4. Load leaderboard
5. Reset game state
6. Spawn initial food

#### Main Game Loop
1. Handle input events
2. Update game state (if not paused/game over)
   - Move snake
   - Update food positions
   - Update visual effects
   - Increment tick counter
3. Draw all game elements
4. Control frame rate

#### Game Over Flow
1. Check if score qualifies for leaderboard
2. If qualified, prompt for initials
3. Save score and initials
4. Display leaderboard
5. Wait for restart input

### 7. Key Features

#### Food System
- **Normal Food**: +1 point, +1 length
- **Golden Food**: +3 points, +1 length
- **Rotten Food**: -1 point, -1 length (minimum 1), spawns bonus foods
- **Moving Food**: Some food items move around the board
- **Concurrent Food**: Bonus foods spawned by rotten food consumption

#### Obstacle System
- Progressive obstacles appear every N foods eaten
- Maximum obstacle limit prevents overcrowding
- BFS ensures food remains accessible
- Obstacles are placed randomly but strategically

#### Speed Progression
- Base speed starts at 4 FPS
- Speed increases by 0.3 per food eaten
- Additional bonus for high scores
- Maximum speed capped at 15 FPS

#### Visual Effects
- Animated gradient background
- Snake head with eyes and animated tongue
- Glowing food effects
- Snake trail effects
- Score-based color progression

#### Sound System
- Programmatically generated tones
- Different sounds for different food types
- Game over sound
- Graceful fallback if sound generation fails

#### Leaderboard System
- Top 5 scores saved to JSON
- Player initials input
- Format migration for backward compatibility
- Reset functionality

### 8. Controls

#### Movement
- Arrow keys or WASD for snake movement
- Direction changes are queued to prevent instant 180° turns

#### Game Control
- **P** or **SPACE**: Pause/unpause
- **R**: Restart when game over
- **L**: Reset leaderboard during gameplay
- **ESC**: Quit game

#### Initials Input
- **ENTER**: Save score with initials
- **BACKSPACE**: Remove last character
- **Letters**: Add characters (uppercase only, max 3)

### 9. Technical Details

#### Data Structures
- **Snake**: `deque` for efficient head/tail operations
- **Obstacles**: `set` for fast collision checking
- **Concurrent Foods**: `list` for bonus foods
- **Leaderboard**: `list` of dictionaries with score/initials

#### Collision Detection
- Wall collision: Check if head is outside grid bounds
- Self collision: Check if head position is in snake body
- Obstacle collision: Check if head position is in obstacles set
- Food collision: Check if head position matches food position

#### Performance Optimizations
- Efficient data structures for collision checking
- Minimal redraws with targeted updates
- Sound generation only when needed
- Trail effects with automatic cleanup

### 10. Error Handling
- Graceful sound system fallback
- File I/O error handling for leaderboard
- Exception handling in sound generation
- Safe obstacle placement with retry logic

This documentation provides a comprehensive overview of the Snake game's architecture, features, and implementation details. The code is well-commented and modular, making it easy to understand and modify.
