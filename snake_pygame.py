#!/usr/bin/env python3
"""
Advanced Snake Game with Pygame
Features: Score tiers, moving food, special foods, obstacles, sound effects, leaderboard
Enhanced with: Snake head visuals, glowing effects, animated background, initials input
"""

# Standard library imports
import pygame          # Main game engine for graphics, sound, and input handling
import random          # For generating random positions and food types
import json           # For saving/loading leaderboard data
import os             # For file system operations (checking if files exist)
import sys            # For system operations (exiting the program)
import math           # For mathematical calculations (sin, cos for animations)
from enum import Enum # For creating enumerated constants (food types)
from typing import List, Tuple, Set, Optional, Dict, Any  # Type hints for better code documentation
from collections import deque  # For efficient snake body management (appendleft/pop operations)

# ==================== GAME CONFIGURATION ====================
# Feature toggles - enable/disable specific game features
FEATURES = {
    "score_tier_colors": True,      # Snake changes color based on score level
    "moving_food": True,            # Food can move around the board
    "special_food": True,           # Enable golden and rotten food types
    "progressive_obstacles": True,  # Obstacles appear as game progresses
    "bounded_grid": True,           # Snake dies when hitting walls (no wrapping)
    "speed_scales_with_eats": True, # Game speed increases with each food eaten
    "sound_effects": True,          # Play sound effects for actions
    "leaderboard": True,            # Save and display high scores
}

# Game balance and tuning parameters
GAME_TUNING = {
    # Grid and display settings
    "grid_cell": 20,                # Size of each grid cell in pixels
    "leaderboard_size": 5,          # Number of top scores to store
    
    # Food behavior settings
    "food_move_every_n_ticks": 6,   # How often moving food changes position
    "special_spawn_chance": 0.22,   # Probability of spawning special food (golden/rotten)
    "rotten_ratio_within_special": 0.35,  # Chance rotten food appears when special food spawns
    
    # Snake settings
    "min_snake_len": 1,             # Minimum snake length (prevents complete elimination)
    
    # Obstacle settings
    "obstacle_every_n_foods": 3,    # Spawn obstacle every N foods eaten
    "max_obstacles": 40,            # Maximum number of obstacles on screen
    
    # Speed progression settings
    "speed_base": 4,                # Starting game speed (frames per second)
    "speed_step_per_food": 0.3,     # Speed increase per food eaten
    "speed_max": 15,                # Maximum game speed cap
    
    # Visual progression settings
    "score_tiers": [0, 5, 10, 20, 35, 50],  # Score thresholds for color changes
    "tier_colors": ["#22c55e", "#3b82f6", "#a855f7", "#f59e0b", "#ef4444", "#eab308"],  # Colors for each tier
}

# ==================== GAME CONSTANTS ====================
# Display and grid constants
WINDOW_SIZE = 600                                    # Game window size (square)
GRID_SIZE = WINDOW_SIZE // GAME_TUNING["grid_cell"]  # Grid dimensions (30x30)
FPS = 120                                            # Target frames per second (not used in main loop)

# ==================== COLOR DEFINITIONS ====================
# Basic colors (RGB tuples)
BLACK = (0, 0, 0)                    # Pure black
WHITE = (255, 255, 255)              # Pure white
GRAY = (128, 128, 128)               # Medium gray
DARK_GRAY = (64, 64, 64)             # Dark gray for obstacles

# Primary game colors
RED = (255, 0, 0)                    # Red for tongue and accents
GREEN = (34, 197, 94)                # #22c55e - Normal food and default snake
BLUE = (59, 130, 246)                # #3b82f6 - Tier color
PURPLE = (168, 85, 247)              # #a855f7 - Tier color
ORANGE = (245, 158, 11)              # #f59e0b - Tier color
YELLOW = (234, 179, 8)               # #eab308 - Tier color
GOLD = (255, 215, 0)                 # Golden food color
BROWN = (139, 69, 19)                # Rotten food color

# Additional colors for visual effects
PINK = (255, 192, 203)               # Pink accent
CYAN = (0, 255, 255)                 # Cyan accent
MAGENTA = (255, 0, 255)              # Magenta accent
LIGHT_BLUE = (173, 216, 230)         # Light blue accent

# ==================== ENUMS AND CONSTANTS ====================
# Food type enumeration - defines the different types of food in the game
class FoodType(Enum):
    NORMAL = "normal"    # Regular food: +1 point, +1 length
    GOLDEN = "golden"    # Special food: +3 points, +1 length
    ROTTEN = "rotten"    # Bad food: -1 point, -1 length (min 1)

# Direction vectors for snake movement (x, y coordinates)
DIRECTIONS = {
    "UP": (0, -1),       # Move up (decrease y)
    "DOWN": (0, 1),      # Move down (increase y)
    "LEFT": (-1, 0),     # Move left (decrease x)
    "RIGHT": (1, 0)      # Move right (increase x)
}

# ==================== FOOD CLASS ====================
class Food:
    """
    Represents food items on the game board.
    Each food has a position, type, movement capability, and color.
    """
    def __init__(self, pos: Tuple[int, int], food_type: FoodType, is_moving: bool = False):
        """
        Initialize a food item.
        
        Args:
            pos: Grid position (x, y) where food is located
            food_type: Type of food (NORMAL, GOLDEN, or ROTTEN)
            is_moving: Whether this food can move around the board
        """
        self.pos = pos                    # Grid position (x, y)
        self.type = food_type             # Food type enum
        self.is_moving = is_moving        # Movement capability flag
        self.color = self._get_color()    # Visual color based on type
    
    def _get_color(self) -> Tuple[int, int, int]:
        """
        Determine the visual color based on food type.
        
        Returns:
            RGB color tuple for rendering
        """
        if self.type == FoodType.NORMAL:
            return GREEN      # Green for normal food
        elif self.type == FoodType.GOLDEN:
            return GOLD       # Gold for special food
        else:  # ROTTEN
            return BROWN      # Brown for rotten food

# ==================== MAIN GAME CLASS ====================
class SnakeGame:
    """
    Main game class that manages the entire Snake game.
    Handles game state, rendering, input, sound, and game logic.
    """
    
    def __init__(self):
        """
        Initialize the Snake game.
        Sets up pygame, creates display, loads assets, and initializes game state.
        """
        # Initialize pygame modules
        pygame.init()                    # Initialize pygame core
        pygame.mixer.init()              # Initialize sound mixer
        
        # Create game display
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))  # Create game window
        pygame.display.set_caption("Advanced Snake Game")                  # Set window title
        self.clock = pygame.time.Clock()                                   # Create clock for FPS control
        
        # Create fonts for text rendering
        self.font = pygame.font.Font(None, 36)        # Main font for score, etc.
        self.small_font = pygame.font.Font(None, 24)  # Smaller font for details
        self.initials_font = pygame.font.Font(None, 48)  # Large font for initials input
        
        # Visual effects state
        self.background_phase = 0.0       # Phase for animated background
        self.tongue_out = False           # Snake tongue animation state
        self.tongue_timer = 0             # Timer for tongue animation
        self.trail_surfaces = []          # List of trail effect surfaces
        self.food_glow_phase = 0.0        # Phase for food glow animation
        
        # Initialize game state
        self.reset()                      # Reset to initial game state
        
        # Load game assets
        self.sounds = self._load_sounds() # Load or create sound effects
        
        # Leaderboard system
        self.leaderboard_file = "leaderboard.json"  # File to store high scores
        self.leaderboard = self._load_leaderboard() # Load existing scores
        
        # Player input state
        self.waiting_for_initials = False # Flag for initials input mode
        self.player_initials = ""         # Current player initials being entered
    
    def _load_sounds(self) -> Dict[str, Optional[pygame.mixer.Sound]]:
        """
        Load or create sound effects for the game.
        If sound files don't exist, generates simple tones programmatically.
        
        Returns:
            Dictionary mapping sound names to pygame Sound objects (or None if failed)
        """
        sounds = {}
        
        # Create simple sound effects using pygame's sound generation
        try:
            # Eat sound (short beep) - A4 note (440 Hz)
            eat_sound = pygame.sndarray.make_sound(
                self._generate_tone(440, 0.1, 44100)  # 440 Hz, 0.1 seconds, 44.1kHz sample rate
            )
            sounds["eat"] = eat_sound
            
            # Golden food sound (higher pitch) - E5 note (660 Hz)
            golden_sound = pygame.sndarray.make_sound(
                self._generate_tone(660, 0.15, 44100)  # 660 Hz, 0.15 seconds
            )
            sounds["golden"] = golden_sound
            
            # Rotten food sound (lower pitch) - A3 note (220 Hz)
            rotten_sound = pygame.sndarray.make_sound(
                self._generate_tone(220, 0.2, 44100)   # 220 Hz, 0.2 seconds
            )
            sounds["rotten"] = rotten_sound
            
            # Game over sound (descending tone) - A4 note (440 Hz)
            game_over_sound = pygame.sndarray.make_sound(
                self._generate_tone(440, 0.5, 44100)   # 440 Hz, 0.5 seconds
            )
            sounds["game_over"] = game_over_sound
            
        except Exception as e:
            # If sound generation fails, disable all sounds
            print(f"Warning: Could not create sound effects: {e}")
            sounds = {key: None for key in ["eat", "golden", "rotten", "game_over"]}
        
        return sounds
    
    def _generate_tone(self, frequency: int, duration: float, sample_rate: int) -> pygame.sndarray.array:
        """
        Generate a simple sine wave tone for sound effects.
        
        Args:
            frequency: Frequency of the tone in Hz
            duration: Duration of the tone in seconds
            sample_rate: Sample rate in Hz (typically 44100)
            
        Returns:
            NumPy array representing the audio data
        """
        import numpy as np
        frames = int(duration * sample_rate)  # Total number of audio frames
        arr = np.zeros((frames, 2))           # Stereo audio array (2 channels)
        
        # Generate sine wave for both channels
        for i in range(frames):
            # Calculate sine wave value and scale to 16-bit range
            wave_value = int(32767 * np.sin(2 * np.pi * frequency * i / sample_rate))
            arr[i][0] = wave_value  # Left channel
            arr[i][1] = wave_value  # Right channel (mono)
        
        return arr.astype(np.int16)  # Convert to 16-bit integer format
    
    def _load_leaderboard(self) -> List[Dict[str, Any]]:
        """
        Load high scores from the leaderboard file.
        Handles both old and new data formats for backward compatibility.
        
        Returns:
            List of score entries, each containing 'score' and 'initials' keys
        """
        try:
            if os.path.exists(self.leaderboard_file):
                with open(self.leaderboard_file, 'r') as f:
                    data = json.load(f)
                    scores = data.get('scores', [])
                    
                    # Ensure all entries are dictionaries (handle format migration)
                    result = []
                    for entry in scores:
                        if isinstance(entry, dict):
                            # New format: already a dictionary
                            result.append(entry)
                        else:
                            # Old format: just a score number, convert to new format
                            result.append({"score": entry, "initials": "AAA"})
                    return result
        except Exception as e:
            print(f"Warning: Could not load leaderboard: {e}")
        return []  # Return empty list if loading fails
    
    def _save_leaderboard(self) -> None:
        """
        Save the current leaderboard to the JSON file.
        Handles file I/O errors gracefully.
        """
        try:
            with open(self.leaderboard_file, 'w') as f:
                json.dump({'scores': self.leaderboard}, f)
        except Exception as e:
            print(f"Warning: Could not save leaderboard: {e}")
    
    def _add_to_leaderboard(self, score: int, initials: str = "AAA") -> None:
        """
        Add a new score to the leaderboard and maintain the top scores list.
        
        Args:
            score: The score to add
            initials: Player initials (defaults to "AAA")
        """
        self.leaderboard.append({"score": score, "initials": initials})
        self.leaderboard.sort(key=lambda x: x["score"], reverse=True)  # Sort by score (highest first)
        self.leaderboard = self.leaderboard[:GAME_TUNING["leaderboard_size"]]  # Keep only top N scores
        self._save_leaderboard()  # Persist to file
    
    def reset_leaderboard(self) -> None:
        """
        Clear all scores from the leaderboard and save the empty state.
        Called when player presses 'L' during gameplay.
        """
        self.leaderboard = []
        self._save_leaderboard()
        print("Leaderboard has been reset!")
    
    def _eat_concurrent_food(self, food: Food) -> None:
        """
        Handle consumption of concurrent food (bonus food spawned by rotten food).
        These are normal or golden foods that appear when rotten food is eaten.
        
        Args:
            food: The concurrent food being eaten
        """
        # Apply score and sound based on food type
        if food.type == FoodType.GOLDEN:
            self.score += 3              # Golden food gives 3 points
            self._play_sound("golden")
        elif food.type == FoodType.NORMAL:
            self.score += 1              # Normal food gives 1 point
            self._play_sound("eat")
        
        self.food_eaten += 1             # Increment food counter
        
        # Update game speed based on food eaten
        if FEATURES["speed_scales_with_eats"]:
            # Gradual speed increase - starts slow, accelerates more slowly
            speed_increase = self.food_eaten * GAME_TUNING["speed_step_per_food"]
            # Add bonus for higher scores to increase difficulty
            if self.food_eaten > 10:
                speed_increase += (self.food_eaten - 10) * 0.1
            
            self.speed = min(
                GAME_TUNING["speed_max"],                    # Cap at maximum speed
                GAME_TUNING["speed_base"] + speed_increase   # Base speed + increase
            )
        
        # Spawn obstacles progressively
        if (FEATURES["progressive_obstacles"] and 
            self.food_eaten % GAME_TUNING["obstacle_every_n_foods"] == 0):
            self.spawn_obstacle()
    
    def reset(self) -> None:
        """
        Reset the game to its initial state.
        Called when starting a new game or restarting after game over.
        """
        # Initialize snake at center of grid
        center_x = GRID_SIZE // 2
        center_y = GRID_SIZE // 2
        self.snake = deque([(center_x, center_y)])  # Snake starts as single segment
        self.direction = DIRECTIONS["RIGHT"]         # Initial movement direction
        self.next_direction = DIRECTIONS["RIGHT"]    # Queued direction change
        
        # Reset game state variables
        self.score = 0                    # Player's current score
        self.food_eaten = 0               # Number of foods consumed
        self.tick_count = 0               # Frame counter for animations
        self.game_over = False            # Game over flag
        self.paused = False               # Pause state flag
        
        # Reset speed to initial value
        self.speed = GAME_TUNING["speed_base"]
        
        # Clear game objects
        self.food = None                                  # No food initially
        self.obstacles: Set[Tuple[int, int]] = set()      # No obstacles initially
        self.concurrent_foods = []                        # No bonus foods initially
        
        # Spawn the first food
        self.spawn_food()
        
        # Reset visual effects and UI state
        self.trail_surfaces = []          # Clear snake trail effects
        self.food_glow_phase = 0.0        # Reset food glow animation
        self.tongue_timer = 0             # Reset tongue animation timer
        self.tongue_out = False           # Reset tongue state
        self.waiting_for_initials = False # Not waiting for player input
        self.player_initials = ""         # Clear player initials
        self.concurrent_foods = []        # Clear bonus foods (redundant but safe)
    
    def spawn_food(self) -> None:
        """
        Spawn a new food item at a random empty position on the grid.
        Determines food type based on probability and spawns accordingly.
        """
        # Determine food type based on probability
        if FEATURES["special_food"] and random.random() < GAME_TUNING["special_spawn_chance"]:
            # Special food spawn chance triggered
            if random.random() < GAME_TUNING["rotten_ratio_within_special"]:
                # Spawn rotten food with bonus normal food
                food_type = FoodType.ROTTEN
                self._spawn_rotten_with_normal()  # Spawns both rotten and normal food
                return
            else:
                # Spawn golden food
                food_type = FoodType.GOLDEN
        else:
            # Spawn normal food
            food_type = FoodType.NORMAL
        
        # Find an empty position on the grid
        while True:
            pos = (
                random.randint(0, GRID_SIZE - 1),  # Random x coordinate
                random.randint(0, GRID_SIZE - 1)   # Random y coordinate
            )
            # Check if position is empty (not occupied by snake, obstacles, or existing food)
            if (pos not in self.snake and 
                pos not in self.obstacles and 
                (self.food is None or pos != self.food.pos)):
                break  # Found empty position
        
        # Determine if this food should move around
        is_moving = FEATURES["moving_food"] and random.random() < 0.3
        
        # Create and place the food
        self.food = Food(pos, food_type, is_moving)
    
    def _spawn_rotten_with_normal(self) -> None:
        """
        Spawn both rotten food and normal food simultaneously.
        This creates a risk/reward scenario where eating rotten food gives penalty
        but also spawns bonus normal food for recovery.
        """
        # Spawn rotten food at random empty position
        while True:
            pos = (
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1)
            )
            if (pos not in self.snake and 
                pos not in self.obstacles and 
                (self.food is None or pos != self.food.pos)):
                break  # Found empty position for rotten food
        
        # Create rotten food with random movement
        is_moving = FEATURES["moving_food"] and random.random() < 0.3
        self.food = Food(pos, FoodType.ROTTEN, is_moving)
        
        # Spawn normal food at a different empty position
        while True:
            pos = (
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1)
            )
            if (pos not in self.snake and 
                pos not in self.obstacles and 
                (self.food is None or pos != self.food.pos)):
                break  # Found empty position for normal food
        
        # Ensure concurrent_foods list exists
        if not hasattr(self, 'concurrent_foods'):
            self.concurrent_foods = []
        
        # Create normal food as concurrent (bonus) food
        is_moving_normal = FEATURES["moving_food"] and random.random() < 0.3
        normal_food = Food(pos, FoodType.NORMAL, is_moving_normal)
        self.concurrent_foods.append(normal_food)
    
    def _spawn_concurrent_food(self) -> None:
        """
        Spawn bonus normal and golden food when rotten food is eaten.
        This provides a recovery mechanism after the penalty from rotten food.
        """
        # Spawn normal food using the regular spawn method
        self.spawn_food()
        
        # Spawn golden food at a different empty position
        while True:
            pos = (
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1)
            )
            if (pos not in self.snake and 
                pos not in self.obstacles and 
                (self.food is None or pos != self.food.pos)):
                break  # Found empty position for golden food
        
        # Create golden food with random movement
        is_moving = FEATURES["moving_food"] and random.random() < 0.3
        golden_food = Food(pos, FoodType.GOLDEN, is_moving)
        
        # Ensure concurrent_foods list exists and add golden food
        if not hasattr(self, 'concurrent_foods'):
            self.concurrent_foods = []
        self.concurrent_foods.append(golden_food)
    
    def spawn_obstacle(self) -> None:
        """
        Spawn a new obstacle at a valid position on the grid.
        Ensures the obstacle doesn't block access to food and doesn't exceed max count.
        """
        # Check if we've reached the maximum obstacle limit
        if len(self.obstacles) >= GAME_TUNING["max_obstacles"]:
            return  # Don't spawn more obstacles
        
        # Try to find a valid position (max 50 attempts)
        for _ in range(50):
            pos = (
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1)
            )
            
            # Check if position is empty and valid
            if (pos not in self.snake and 
                pos not in self.obstacles and 
                (self.food is None or pos != self.food.pos)):
                
                # Ensure this obstacle won't block access to food
                if self._is_food_accessible(pos):
                    self.obstacles.add(pos)  # Add obstacle to the set
                    break  # Successfully placed obstacle
    
    def _is_food_accessible(self, new_obstacle: Tuple[int, int]) -> bool:
        """
        Check if food is still accessible after adding a new obstacle.
        Uses BFS (Breadth-First Search) to ensure there's a path from snake to food.
        
        Args:
            new_obstacle: Position where the new obstacle would be placed
            
        Returns:
            True if food is accessible, False if blocked
        """
        if self.food is None:
            return True  # No food to reach
        
        # BFS to check connectivity from snake head to food
        visited = set()                    # Track visited positions
        queue = deque([self.snake[0]])     # Start BFS from snake head
        visited.add(self.snake[0])
        
        while queue:
            current = queue.popleft()
            if current == self.food.pos:
                return True  # Found path to food
            
            # Check all four directions from current position
            for dx, dy in DIRECTIONS.values():
                next_pos = (current[0] + dx, current[1] + dy)
                
                # Check if next position is valid and unvisited
                if (0 <= next_pos[0] < GRID_SIZE and 
                    0 <= next_pos[1] < GRID_SIZE and
                    next_pos not in visited and
                    next_pos not in self.snake and
                    next_pos not in self.obstacles and
                    next_pos != new_obstacle):  # Don't include the new obstacle
                    visited.add(next_pos)
                    queue.append(next_pos)
        
        return False  # No path found to food
    
    def move_snake(self) -> None:
        """
        Move the snake one step in the current direction.
        Handles collision detection, food consumption, and snake growth.
        """
        # Don't move if game is over or paused
        if self.game_over or self.paused:
            return
        
        # Update direction from queued direction change
        self.direction = self.next_direction
        
        # Calculate new head position
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        # Check wall collision (bounded grid)
        if (new_head[0] < 0 or new_head[0] >= GRID_SIZE or 
            new_head[1] < 0 or new_head[1] >= GRID_SIZE):
            self.game_over = True
            self._play_sound("game_over")
            return
        
        # Check self collision (snake hitting itself)
        if new_head in self.snake:
            self.game_over = True
            self._play_sound("game_over")
            return
        
        # Check obstacle collision
        if new_head in self.obstacles:
            self.game_over = True
            self._play_sound("game_over")
            return
        
        # Move snake by adding new head
        self.snake.appendleft(new_head)
        
        # Check for food consumption
        food_eaten = False
        
        # Check main food collision
        if self.food and new_head == self.food.pos:
            self._eat_food()
            food_eaten = True
        
        # Check concurrent food collision (bonus foods)
        for i, concurrent_food in enumerate(self.concurrent_foods):
            if new_head == concurrent_food.pos:
                self._eat_concurrent_food(concurrent_food)
                self.concurrent_foods.pop(i)  # Remove eaten concurrent food
                food_eaten = True
                break
        
        # If no food was eaten, remove tail (snake doesn't grow)
        if not food_eaten:
            self.snake.pop()
    
    def _eat_food(self) -> None:
        """
        Handle consumption of the main food item.
        Applies score changes, sound effects, and game progression.
        """
        if not self.food:
            return  # No food to eat
        
        food_type = self.food.type
        
        # Apply effects based on food type
        if food_type == FoodType.NORMAL:
            self.score += 1              # Normal food: +1 point
            self._play_sound("eat")
        elif food_type == FoodType.GOLDEN:
            self.score += 3              # Golden food: +3 points
            self._play_sound("golden")
        elif food_type == FoodType.ROTTEN:
            self.score = max(0, self.score - 1)  # Rotten food: -1 point (minimum 0)
            self._play_sound("rotten")
            
            # Shrink snake if possible (minimum length protection)
            if len(self.snake) > GAME_TUNING["min_snake_len"]:
                self.snake.pop()
            
            # Spawn bonus foods for recovery
            self._spawn_concurrent_food()
            return  # Skip normal progression since we handled it above
        
        self.food_eaten += 1  # Increment food counter
        
        # Update game speed based on food eaten
        if FEATURES["speed_scales_with_eats"]:
            # Gradual speed increase - starts slow, accelerates more slowly
            speed_increase = self.food_eaten * GAME_TUNING["speed_step_per_food"]
            # Add bonus for higher scores to increase difficulty
            if self.food_eaten > 10:
                speed_increase += (self.food_eaten - 10) * 0.1
            
            self.speed = min(
                GAME_TUNING["speed_max"],                    # Cap at maximum speed
                GAME_TUNING["speed_base"] + speed_increase   # Base speed + increase
            )
        
        # Spawn new food for next round
        self.spawn_food()
        
        # Spawn obstacles progressively
        if (FEATURES["progressive_obstacles"] and 
            self.food_eaten % GAME_TUNING["obstacle_every_n_foods"] == 0):
            self.spawn_obstacle()
    
    def _play_sound(self, sound_name: str) -> None:
        """
        Play a sound effect if available and sound effects are enabled.
        
        Args:
            sound_name: Name of the sound to play (e.g., "eat", "golden", "rotten", "game_over")
        """
        if FEATURES["sound_effects"] and self.sounds.get(sound_name):
            try:
                self.sounds[sound_name].play()
            except Exception:
                pass  # Ignore sound errors silently
    
    def update_food(self) -> None:
        """
        Update the position of moving food items.
        Moves food to adjacent empty cells if possible.
        """
        # Check if food exists, is moving, and it's time to move
        if (self.food and self.food.is_moving and 
            self.tick_count % GAME_TUNING["food_move_every_n_ticks"] == 0):
            
            # Try to move food to an adjacent empty cell
            directions = list(DIRECTIONS.values())
            random.shuffle(directions)  # Randomize direction selection
            
            # Try each direction until we find a valid move
            for dx, dy in directions:
                new_pos = (self.food.pos[0] + dx, self.food.pos[1] + dy)
                
                # Check if new position is valid (within bounds and empty)
                if (0 <= new_pos[0] < GRID_SIZE and 
                    0 <= new_pos[1] < GRID_SIZE and
                    new_pos not in self.snake and 
                    new_pos not in self.obstacles):
                    self.food.pos = new_pos  # Move food to new position
                    break  # Successfully moved, stop trying other directions
    
    def get_snake_color(self, score: int) -> Tuple[int, int, int]:
        """
        Get the snake color based on the current score tier.
        Snake changes color as the player progresses through score levels.
        
        Args:
            score: Current player score
            
        Returns:
            RGB color tuple for the snake
        """
        if not FEATURES["score_tier_colors"]:
            return GREEN  # Default color if tier colors disabled
        
        tiers = GAME_TUNING["score_tiers"]      # Score thresholds
        colors = GAME_TUNING["tier_colors"]     # Corresponding colors
        
        # Find the highest tier the score qualifies for
        for i in range(len(tiers) - 1, -1, -1):
            if score >= tiers[i]:
                color_hex = colors[i]
                # Convert hex color to RGB tuple
                return tuple(int(color_hex[j:j+2], 16) for j in (1, 3, 5))
        
        return GREEN  # Default color if no tier matched
    
    def _draw_animated_background(self) -> None:
        """
        Draw an animated gradient background with shifting colors.
        Creates a smooth color transition effect over time.
        """
        self.background_phase += 0.01  # Increment animation phase
        
        # Create gradient colors that shift over time
        phase = self.background_phase % (2 * math.pi)
        
        # Color transitions: blue -> purple -> pink -> back to blue
        r = int(128 + 127 * math.sin(phase))                    # Red component
        g = int(64 + 64 * math.sin(phase + 2 * math.pi / 3))   # Green component (120° offset)
        b = int(192 + 63 * math.sin(phase + 4 * math.pi / 3))  # Blue component (240° offset)
        
        # Create gradient surface
        gradient_surface = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        
        # Draw vertical gradient with variation
        for y in range(WINDOW_SIZE):
            # Add some variation based on y position for more interesting effect
            intensity = 0.7 + 0.3 * math.sin(y * 0.01 + phase)
            color = (
                int(r * intensity),
                int(g * intensity),
                int(b * intensity)
            )
            pygame.draw.line(gradient_surface, color, (0, y), (WINDOW_SIZE, y))
        
        # Blit the gradient to the screen
        self.screen.blit(gradient_surface, (0, 0))
        
        # Grid lines removed as requested
    
    def _draw_snake_head(self, head_pos: Tuple[int, int], direction: Tuple[int, int], color: Tuple[int, int, int]) -> None:
        """
        Draw the snake head with eyes and animated tongue.
        Creates a more detailed and animated snake head compared to body segments.
        
        Args:
            head_pos: Grid position (x, y) of the head
            direction: Current movement direction
            color: RGB color for the head
        """
        x, y = head_pos
        cell_size = GAME_TUNING["grid_cell"]
        
        # Calculate head center for positioning eyes and tongue
        center_x = x * cell_size + cell_size // 2
        center_y = y * cell_size + cell_size // 2
        
        # Draw head body (slightly larger than body segments)
        head_rect = pygame.Rect(
            x * cell_size + 2,      # Slightly inset from grid
            y * cell_size + 2,
            cell_size - 4,          # Slightly smaller than full cell
            cell_size - 4
        )
        pygame.draw.rect(self.screen, color, head_rect)
        
        # Calculate rotation angle based on direction (for reference)
        if direction == DIRECTIONS["RIGHT"]:
            angle = 0
        elif direction == DIRECTIONS["DOWN"]:
            angle = 90
        elif direction == DIRECTIONS["LEFT"]:
            angle = 180
        else:  # UP
            angle = 270
        
        # Draw eyes
        eye_offset = cell_size // 4  # Distance from center
        eye_size = 3                 # Eye radius
        
        # Calculate eye positions based on direction
        if direction == DIRECTIONS["RIGHT"]:
            eye1_pos = (center_x - eye_offset, center_y - eye_offset)
            eye2_pos = (center_x - eye_offset, center_y + eye_offset)
        elif direction == DIRECTIONS["DOWN"]:
            eye1_pos = (center_x - eye_offset, center_y - eye_offset)
            eye2_pos = (center_x + eye_offset, center_y - eye_offset)
        elif direction == DIRECTIONS["LEFT"]:
            eye1_pos = (center_x + eye_offset, center_y - eye_offset)
            eye2_pos = (center_x + eye_offset, center_y + eye_offset)
        else:  # UP
            eye1_pos = (center_x - eye_offset, center_y + eye_offset)
            eye2_pos = (center_x + eye_offset, center_y + eye_offset)
        
        # Draw white eyes
        pygame.draw.circle(self.screen, WHITE, eye1_pos, eye_size)
        pygame.draw.circle(self.screen, WHITE, eye2_pos, eye_size)
        
        # Draw black pupils
        pygame.draw.circle(self.screen, BLACK, eye1_pos, eye_size - 1)
        pygame.draw.circle(self.screen, BLACK, eye2_pos, eye_size - 1)
        
        # Draw animated tongue (flicking in and out)
        self.tongue_timer += 1
        if self.tongue_timer > 30:  # Change every 30 ticks
            self.tongue_out = not self.tongue_out
            self.tongue_timer = 0
        
        if self.tongue_out:
            # Calculate tongue position based on direction
            tongue_length = cell_size // 3
            if direction == DIRECTIONS["RIGHT"]:
                tongue_start = (center_x + cell_size // 2 - 2, center_y)
                tongue_end = (center_x + cell_size // 2 + tongue_length, center_y)
            elif direction == DIRECTIONS["DOWN"]:
                tongue_start = (center_x, center_y + cell_size // 2 - 2)
                tongue_end = (center_x, center_y + cell_size // 2 + tongue_length)
            elif direction == DIRECTIONS["LEFT"]:
                tongue_start = (center_x - cell_size // 2 + 2, center_y)
                tongue_end = (center_x - cell_size // 2 - tongue_length, center_y)
            else:  # UP
                tongue_start = (center_x, center_y - cell_size // 2 + 2)
                tongue_end = (center_x, center_y - cell_size // 2 - tongue_length)
            
            # Draw forked tongue
            pygame.draw.line(self.screen, RED, tongue_start, tongue_end, 2)
            # Draw tongue fork
            fork_offset = 2
            if direction in [DIRECTIONS["RIGHT"], DIRECTIONS["LEFT"]]:
                pygame.draw.line(self.screen, RED, 
                               (tongue_end[0], tongue_end[1] - fork_offset), 
                               (tongue_end[0], tongue_end[1] + fork_offset), 2)
            else:
                pygame.draw.line(self.screen, RED, 
                               (tongue_end[0] - fork_offset, tongue_end[1]), 
                               (tongue_end[0] + fork_offset, tongue_end[1]), 2)
    
    def _draw_glowing_food(self, food: Food) -> None:
        """Draw food with glowing effect"""
        if not food:
            return
        
        x, y = food.pos
        cell_size = GAME_TUNING["grid_cell"]
        center_x = x * cell_size + cell_size // 2
        center_y = y * cell_size + cell_size // 2
        
        # Update glow phase
        self.food_glow_phase += 0.2
        
        # Calculate glow intensity
        if food.type == FoodType.NORMAL:
            # Pulsing glow
            glow_intensity = 0.5 + 0.5 * math.sin(self.food_glow_phase)
            glow_color = tuple(int(c * glow_intensity) for c in food.color)
            glow_size = int(cell_size * (0.8 + 0.4 * glow_intensity))
        elif food.type == FoodType.GOLDEN:
            # Brighter yellow glow
            glow_intensity = 0.7 + 0.3 * math.sin(self.food_glow_phase)
            glow_color = tuple(int(c * glow_intensity) for c in food.color)
            glow_size = int(cell_size * (0.9 + 0.6 * glow_intensity))
        else:  # ROTTEN
            # Flicker effect
            glow_intensity = 0.3 + 0.4 * abs(math.sin(self.food_glow_phase * 3))
            glow_color = tuple(int(c * glow_intensity) for c in food.color)
            glow_size = int(cell_size * (0.6 + 0.3 * glow_intensity))
        
        # Draw glow effect (multiple circles with decreasing alpha)
        for i in range(3):
            alpha = int(50 * (1 - i / 3))
            glow_surface = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            glow_rect = pygame.Rect(0, 0, glow_size * 2, glow_size * 2)
            glow_rect.center = (glow_size, glow_size)
            pygame.draw.ellipse(glow_surface, (*glow_color, alpha), glow_rect)
            self.screen.blit(glow_surface, (center_x - glow_size, center_y - glow_size))
        
        # Draw main food
        food_rect = pygame.Rect(
            x * cell_size + 2,
            y * cell_size + 2,
            cell_size - 4,
            cell_size - 4
        )
        pygame.draw.rect(self.screen, food.color, food_rect)
    
    def _update_trail_effect(self) -> None:
        """Update snake trail effect"""
        if len(self.snake) < 2:
            return
        
        # Create trail surface for current head position
        head_pos = self.snake[0]
        trail_surface = pygame.Surface((GAME_TUNING["grid_cell"], GAME_TUNING["grid_cell"]), pygame.SRCALPHA)
        
        # Get snake color
        snake_color = self.get_snake_color(self.score)
        
        # Create fading trail effect
        for i in range(5):
            alpha = int(50 * (1 - i / 5))
            trail_color = (*snake_color, alpha)
            trail_rect = pygame.Rect(i, i, GAME_TUNING["grid_cell"] - 2*i, GAME_TUNING["grid_cell"] - 2*i)
            pygame.draw.rect(trail_surface, trail_color, trail_rect)
        
        # Store trail surface with position
        self.trail_surfaces.append({
            'surface': trail_surface,
            'pos': head_pos,
            'life': 20  # Trail lasts 20 frames
        })
        
        # Update and remove old trail surfaces
        self.trail_surfaces = [trail for trail in self.trail_surfaces if trail['life'] > 0]
        for trail in self.trail_surfaces:
            trail['life'] -= 1
    
    def handle_events(self) -> None:
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if not self.waiting_for_initials:
                    self._add_to_leaderboard(self.score, self.player_initials)
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not self.waiting_for_initials:
                        self._add_to_leaderboard(self.score, self.player_initials)
                    pygame.quit()
                    sys.exit()
                
                elif event.key == pygame.K_r and self.game_over and not self.waiting_for_initials:
                    self.reset()
                
                elif event.key == pygame.K_l and not self.game_over and not self.paused:
                    # Reset leaderboard with L key during gameplay
                    self.reset_leaderboard()
                
                elif event.key == pygame.K_SPACE and not self.game_over and not self.paused:
                    self.paused = not self.paused
                
                elif event.key == pygame.K_p and not self.game_over:
                    # Pause/unpause with P key
                    self.paused = not self.paused
                
                elif self.waiting_for_initials:
                    # Handle initials input
                    if event.key == pygame.K_RETURN:
                        # Save score with initials
                        self._add_to_leaderboard(self.score, self.player_initials)
                        self.waiting_for_initials = False
                        self.reset()
                    elif event.key == pygame.K_BACKSPACE:
                        # Remove last character
                        self.player_initials = self.player_initials[:-1]
                    elif event.unicode.isalpha() and len(self.player_initials) < 3:
                        # Add character (uppercase only)
                        self.player_initials += event.unicode.upper()
                
                elif not self.game_over and not self.paused and not self.waiting_for_initials:
                    # Movement controls
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        if self.direction != DIRECTIONS["DOWN"]:
                            self.next_direction = DIRECTIONS["UP"]
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        if self.direction != DIRECTIONS["UP"]:
                            self.next_direction = DIRECTIONS["DOWN"]
                    elif event.key in [pygame.K_LEFT, pygame.K_a]:
                        if self.direction != DIRECTIONS["RIGHT"]:
                            self.next_direction = DIRECTIONS["LEFT"]
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        if self.direction != DIRECTIONS["LEFT"]:
                            self.next_direction = DIRECTIONS["RIGHT"]
    
    def draw(self) -> None:
        """Draw the game"""
        # Draw animated background
        self._draw_animated_background()
        
        # Draw trail effects
        for trail in self.trail_surfaces:
            x, y = trail['pos']
            self.screen.blit(trail['surface'], 
                           (x * GAME_TUNING["grid_cell"], y * GAME_TUNING["grid_cell"]))
        
        # Draw obstacles
        for obstacle in self.obstacles:
            rect = pygame.Rect(
                obstacle[0] * GAME_TUNING["grid_cell"],
                obstacle[1] * GAME_TUNING["grid_cell"],
                GAME_TUNING["grid_cell"],
                GAME_TUNING["grid_cell"]
            )
            pygame.draw.rect(self.screen, DARK_GRAY, rect)
        
        # Draw snake body (excluding head)
        snake_color = self.get_snake_color(self.score)
        snake_list = list(self.snake)
        for i, segment in enumerate(snake_list[1:], 1):  # Skip head
            rect = pygame.Rect(
                segment[0] * GAME_TUNING["grid_cell"],
                segment[1] * GAME_TUNING["grid_cell"],
                GAME_TUNING["grid_cell"],
                GAME_TUNING["grid_cell"]
            )
            pygame.draw.rect(self.screen, snake_color, rect)
        
        # Draw snake head with special visuals
        if self.snake:
            self._draw_snake_head(self.snake[0], self.direction, snake_color)
        
        # Draw glowing food
        if self.food:
            self._draw_glowing_food(self.food)
        
        # Draw concurrent foods (golden food from rotten food consumption)
        for concurrent_food in self.concurrent_foods:
            self._draw_glowing_food(concurrent_food)
        
        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Draw speed
        speed_text = self.small_font.render(f"Speed: {self.speed:.1f}", True, WHITE)
        self.screen.blit(speed_text, (10, 50))
        
        # Draw concurrent food count
        if self.concurrent_foods:
            # Count different types of concurrent foods
            normal_count = sum(1 for food in self.concurrent_foods if food.type == FoodType.NORMAL)
            golden_count = sum(1 for food in self.concurrent_foods if food.type == FoodType.GOLDEN)
            
            if normal_count > 0:
                normal_text = self.small_font.render(f"Normal Foods: {normal_count}", True, WHITE)
                self.screen.blit(normal_text, (10, 80))
            if golden_count > 0:
                golden_text = self.small_font.render(f"Golden Foods: {golden_count}", True, WHITE)
                y_offset = 80 if normal_count > 0 else 80
                self.screen.blit(golden_text, (10, y_offset + 20))
        
        # Draw pause indicator
        if self.paused:
            pause_text = self.font.render("PAUSED", True, WHITE)
            text_rect = pause_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2))
            self.screen.blit(pause_text, text_rect)
            
            # Show pause instructions
            pause_instructions = self.small_font.render("Press P or SPACE to unpause", True, WHITE)
            instructions_rect = pause_instructions.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 40))
            self.screen.blit(pause_instructions, instructions_rect)
        
        # Draw game over overlay
        if self.game_over:
            self._draw_game_over()
        
        # Draw initials input
        if self.waiting_for_initials:
            self._draw_initials_input()
        
        pygame.display.flip()
    
    def _draw_game_over(self) -> None:
        """Draw game over overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        game_over_text = self.font.render("GAME OVER", True, WHITE)
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        
        # Center the text
        game_over_rect = game_over_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 - 80))
        score_rect = score_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 - 40))
        
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(score_text, score_rect)
        
        # Check if score qualifies for leaderboard
        qualifies = False
        if FEATURES["leaderboard"]:
            if len(self.leaderboard) < GAME_TUNING["leaderboard_size"]:
                qualifies = True
            elif self.leaderboard:
                # Get the lowest score from leaderboard
                lowest_score = min(entry["score"] for entry in self.leaderboard)
                qualifies = self.score > lowest_score
        
        if qualifies:
            # Ask for initials
            initials_text = self.small_font.render("Enter your initials (3 letters):", True, WHITE)
            initials_rect = initials_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 10))
            self.screen.blit(initials_text, initials_rect)
            
            # Show current initials
            current_initials = self.player_initials.ljust(3, '_')
            initials_display = self.initials_font.render(current_initials, True, WHITE)
            initials_display_rect = initials_display.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 50))
            self.screen.blit(initials_display, initials_display_rect)
            
            # Instructions
            enter_text = self.small_font.render("Press ENTER to save, R to restart", True, WHITE)
            enter_rect = enter_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 90))
            self.screen.blit(enter_text, enter_rect)
            
            # Set waiting for initials flag
            self.waiting_for_initials = True
        else:
            # Instructions
            restart_text = self.small_font.render("Press R to restart, ESC to quit", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 20))
            self.screen.blit(restart_text, restart_rect)
            
            # Leaderboard reset instruction
            reset_text = self.small_font.render("Press L during gameplay to reset leaderboard", True, WHITE)
            reset_rect = reset_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 50))
            self.screen.blit(reset_text, reset_rect)
        
        # Draw leaderboard
        if FEATURES["leaderboard"] and self.leaderboard:
            self._draw_leaderboard()
    
    def _draw_leaderboard(self) -> None:
        """Draw leaderboard on game over screen"""
        leaderboard_text = self.small_font.render("LEADERBOARD", True, WHITE)
        leaderboard_rect = leaderboard_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 120))
        self.screen.blit(leaderboard_text, leaderboard_rect)
        
        # Draw top scores with initials
        for i, entry in enumerate(self.leaderboard[:5]):
            if isinstance(entry, dict):
                initials = entry.get("initials", "AAA")
                score = entry.get("score", 0)
                rank_text = self.small_font.render(f"{i+1}. {initials} - {score}", True, WHITE)
            else:
                # Legacy support for old format
                rank_text = self.small_font.render(f"{i+1}. AAA - {entry}", True, WHITE)
            rank_rect = rank_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2 + 150 + i * 25))
            self.screen.blit(rank_text, rank_rect)
    
    def _draw_initials_input(self) -> None:
        """Draw initials input screen"""
        # This method is called when waiting_for_initials is True
        # The actual drawing is handled in _draw_game_over()
        pass
    
    def run(self) -> None:
        """Main game loop"""
        while True:
            self.handle_events()
            
            if not self.game_over and not self.paused and not self.waiting_for_initials:
                self.move_snake()
                self.update_food()
                self._update_trail_effect()
                self.tick_count += 1
            elif self.game_over and not self.waiting_for_initials:
                # Check if we should ask for initials
                qualifies = False
                if FEATURES["leaderboard"]:
                    if len(self.leaderboard) < GAME_TUNING["leaderboard_size"]:
                        qualifies = True
                    elif self.leaderboard:
                        # Get the lowest score from leaderboard
                        lowest_score = min(entry["score"] for entry in self.leaderboard)
                        qualifies = self.score > lowest_score
                
                if qualifies:
                    self.waiting_for_initials = True
            
            self.draw()
            self.clock.tick(self.speed)

def main():
    """Main function"""
    try:
        game = SnakeGame()
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        import traceback
        print(f"Error running game: {e}")
        print("Full traceback:")
        traceback.print_exc()
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
