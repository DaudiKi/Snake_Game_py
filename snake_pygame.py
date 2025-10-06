#!/usr/bin/env python3
"""
Advanced Snake Game with Pygame
Features: Score tiers, moving food, special foods, obstacles, sound effects, leaderboard
Enhanced with: Snake head visuals, glowing effects, animated background, initials input
"""

import pygame
import random
import json
import os
import sys
import math
from enum import Enum
from typing import List, Tuple, Set, Optional, Dict, Any
from collections import deque

# Configuration
FEATURES = {
    "score_tier_colors": True,
    "moving_food": True,
    "special_food": True,
    "progressive_obstacles": True,
    "bounded_grid": True,
    "speed_scales_with_eats": True,
    "sound_effects": True,
    "leaderboard": True,
}

GAME_TUNING = {
    "grid_cell": 20,
    "food_move_every_n_ticks": 6,
    "special_spawn_chance": 0.22,
    "rotten_ratio_within_special": 0.35,
    "min_snake_len": 1,
    "obstacle_every_n_foods": 3,
    "max_obstacles": 40,
    "speed_base": 4,  # Much slower starting speed
    "speed_step_per_food": 0.3,  # Smaller increments
    "speed_max": 15,  # Lower maximum speed
    "score_tiers": [0, 5, 10, 20, 35, 50],
    "tier_colors": ["#22c55e", "#3b82f6", "#a855f7", "#f59e0b", "#ef4444", "#eab308"],
    "leaderboard_size": 5,  # store top 5 scores
}

# Constants
WINDOW_SIZE = 600
GRID_SIZE = WINDOW_SIZE // GAME_TUNING["grid_cell"]  # 30x30 grid
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (34, 197, 94)  # #22c55e
BLUE = (59, 130, 246)  # #3b82f6
PURPLE = (168, 85, 247)  # #a855f7
ORANGE = (245, 158, 11)  # #f59e0b
YELLOW = (234, 179, 8)  # #eab308
GOLD = (255, 215, 0)
BROWN = (139, 69, 19)

# Additional colors for visual effects
PINK = (255, 192, 203)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
LIGHT_BLUE = (173, 216, 230)

# Food types
class FoodType(Enum):
    NORMAL = "normal"
    GOLDEN = "golden"
    ROTTEN = "rotten"

# Direction vectors
DIRECTIONS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0)
}

class Food:
    """Represents food on the game board"""
    def __init__(self, pos: Tuple[int, int], food_type: FoodType, is_moving: bool = False):
        self.pos = pos
        self.type = food_type
        self.is_moving = is_moving
        self.color = self._get_color()
    
    def _get_color(self) -> Tuple[int, int, int]:
        """Get color based on food type"""
        if self.type == FoodType.NORMAL:
            return GREEN
        elif self.type == FoodType.GOLDEN:
            return GOLD
        else:  # ROTTEN
            return BROWN

class SnakeGame:
    """Main game class for the Snake game"""
    
    def __init__(self):
        """Initialize the game"""
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption("Advanced Snake Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Visual effects
        self.background_phase = 0.0
        self.tongue_out = False
        self.tongue_timer = 0
        self.trail_surfaces = []  # For snake trail effect
        self.food_glow_phase = 0.0
        
        # Game state
        self.reset()
        
        # Sound effects
        self.sounds = self._load_sounds()
        
        # Leaderboard
        self.leaderboard_file = "leaderboard.json"
        self.leaderboard = self._load_leaderboard()
        
        # Player initials input
        self.waiting_for_initials = False
        self.player_initials = ""
        self.initials_font = pygame.font.Font(None, 48)
    
    def _load_sounds(self) -> Dict[str, Optional[pygame.mixer.Sound]]:
        """Load sound effects (create simple tones if files don't exist)"""
        sounds = {}
        
        # Create simple sound effects using pygame's sound generation
        try:
            # Eat sound (short beep)
            eat_sound = pygame.sndarray.make_sound(
                self._generate_tone(440, 0.1, 44100)  # A4 note
            )
            sounds["eat"] = eat_sound
            
            # Golden food sound (higher pitch)
            golden_sound = pygame.sndarray.make_sound(
                self._generate_tone(660, 0.15, 44100)  # E5 note
            )
            sounds["golden"] = golden_sound
            
            # Rotten food sound (lower pitch)
            rotten_sound = pygame.sndarray.make_sound(
                self._generate_tone(220, 0.2, 44100)  # A3 note
            )
            sounds["rotten"] = rotten_sound
            
            # Game over sound (descending tone)
            game_over_sound = pygame.sndarray.make_sound(
                self._generate_tone(440, 0.5, 44100)  # Longer A4
            )
            sounds["game_over"] = game_over_sound
            
        except Exception as e:
            print(f"Warning: Could not create sound effects: {e}")
            sounds = {key: None for key in ["eat", "golden", "rotten", "game_over"]}
        
        return sounds
    
    def _generate_tone(self, frequency: int, duration: float, sample_rate: int) -> pygame.sndarray.array:
        """Generate a simple tone for sound effects"""
        import numpy as np
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2))
        
        for i in range(frames):
            arr[i][0] = int(32767 * np.sin(2 * np.pi * frequency * i / sample_rate))
            arr[i][1] = int(32767 * np.sin(2 * np.pi * frequency * i / sample_rate))
        
        return arr.astype(np.int16)
    
    def _load_leaderboard(self) -> List[Dict[str, Any]]:
        """Load leaderboard from file"""
        try:
            if os.path.exists(self.leaderboard_file):
                with open(self.leaderboard_file, 'r') as f:
                    data = json.load(f)
                    scores = data.get('scores', [])
                    # Ensure all entries are dictionaries
                    result = []
                    for entry in scores:
                        if isinstance(entry, dict):
                            result.append(entry)
                        else:
                            # Convert old format to new format
                            result.append({"score": entry, "initials": "AAA"})
                    return result
        except Exception as e:
            print(f"Warning: Could not load leaderboard: {e}")
        return []
    
    def _save_leaderboard(self) -> None:
        """Save leaderboard to file"""
        try:
            with open(self.leaderboard_file, 'w') as f:
                json.dump({'scores': self.leaderboard}, f)
        except Exception as e:
            print(f"Warning: Could not save leaderboard: {e}")
    
    def _add_to_leaderboard(self, score: int, initials: str = "AAA") -> None:
        """Add score to leaderboard if it qualifies"""
        self.leaderboard.append({"score": score, "initials": initials})
        self.leaderboard.sort(key=lambda x: x["score"], reverse=True)
        self.leaderboard = self.leaderboard[:GAME_TUNING["leaderboard_size"]]
        self._save_leaderboard()
    
    def reset_leaderboard(self) -> None:
        """Reset the leaderboard/scorecards"""
        self.leaderboard = []
        self._save_leaderboard()
        print("Leaderboard has been reset!")
    
    def _eat_concurrent_food(self, food: Food) -> None:
        """Handle concurrent food consumption (golden food from rotten food)"""
        if food.type == FoodType.GOLDEN:
            self.score += 3
            self._play_sound("golden")
        
        self.food_eaten += 1
        
        # Update speed with more gradual progression
        if FEATURES["speed_scales_with_eats"]:
            # More gradual speed increase - starts slow, accelerates more slowly
            speed_increase = self.food_eaten * GAME_TUNING["speed_step_per_food"]
            # Add a small bonus for higher scores to make it more challenging
            if self.food_eaten > 10:
                speed_increase += (self.food_eaten - 10) * 0.1
            
            self.speed = min(
                GAME_TUNING["speed_max"],
                GAME_TUNING["speed_base"] + speed_increase
            )
        
        # Spawn obstacles
        if (FEATURES["progressive_obstacles"] and 
            self.food_eaten % GAME_TUNING["obstacle_every_n_foods"] == 0):
            self.spawn_obstacle()
    
    def reset(self) -> None:
        """Reset the game to initial state"""
        # Snake starts in the center
        center_x = GRID_SIZE // 2
        center_y = GRID_SIZE // 2
        self.snake = deque([(center_x, center_y)])
        self.direction = DIRECTIONS["RIGHT"]
        self.next_direction = DIRECTIONS["RIGHT"]
        
        # Game state
        self.score = 0
        self.food_eaten = 0
        self.tick_count = 0
        self.game_over = False
        self.paused = False
        
        # Speed calculation
        self.speed = GAME_TUNING["speed_base"]
        
        # Food and obstacles
        self.food = None
        self.obstacles: Set[Tuple[int, int]] = set()
        self.concurrent_foods = []  # For concurrent food spawning
        
        # Spawn initial food
        self.spawn_food()
        
        # Reset visual effects
        self.trail_surfaces = []
        self.food_glow_phase = 0.0
        self.tongue_timer = 0
        self.tongue_out = False
        self.waiting_for_initials = False
        self.player_initials = ""
        self.concurrent_foods = []
    
    def spawn_food(self) -> None:
        """Spawn food at a random empty position"""
        # Determine food type
        if FEATURES["special_food"] and random.random() < GAME_TUNING["special_spawn_chance"]:
            if random.random() < GAME_TUNING["rotten_ratio_within_special"]:
                food_type = FoodType.ROTTEN
            else:
                food_type = FoodType.GOLDEN
        else:
            food_type = FoodType.NORMAL
        
        # Find empty position
        while True:
            pos = (
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1)
            )
            if (pos not in self.snake and 
                pos not in self.obstacles and 
                (self.food is None or pos != self.food.pos)):
                break
        
        # Determine if food should move
        is_moving = FEATURES["moving_food"] and random.random() < 0.3
        
        self.food = Food(pos, food_type, is_moving)
    
    def _spawn_concurrent_food(self) -> None:
        """Spawn normal and golden food when rotten food is eaten"""
        # Spawn normal food
        self.spawn_food()
        
        # Spawn golden food at a different position
        while True:
            pos = (
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1)
            )
            if (pos not in self.snake and 
                pos not in self.obstacles and 
                (self.food is None or pos != self.food.pos)):
                break
        
        # Create golden food
        is_moving = FEATURES["moving_food"] and random.random() < 0.3
        golden_food = Food(pos, FoodType.GOLDEN, is_moving)
        
        # Store the golden food as a special concurrent food
        if not hasattr(self, 'concurrent_foods'):
            self.concurrent_foods = []
        self.concurrent_foods.append(golden_food)
    
    def spawn_obstacle(self) -> None:
        """Spawn an obstacle at a valid position"""
        if len(self.obstacles) >= GAME_TUNING["max_obstacles"]:
            return
        
        # Try to find a valid position
        for _ in range(50):  # Max attempts
            pos = (
                random.randint(0, GRID_SIZE - 1),
                random.randint(0, GRID_SIZE - 1)
            )
            
            # Check if position is valid
            if (pos not in self.snake and 
                pos not in self.obstacles and 
                (self.food is None or pos != self.food.pos)):
                
                # Check if this would block food access (basic BFS)
                if self._is_food_accessible(pos):
                    self.obstacles.add(pos)
                    break
    
    def _is_food_accessible(self, new_obstacle: Tuple[int, int]) -> bool:
        """Check if food is still accessible after adding obstacle"""
        if self.food is None:
            return True
        
        # Simple BFS to check connectivity
        visited = set()
        queue = deque([self.snake[0]])  # Start from snake head
        visited.add(self.snake[0])
        
        while queue:
            current = queue.popleft()
            if current == self.food.pos:
                return True
            
            for dx, dy in DIRECTIONS.values():
                next_pos = (current[0] + dx, current[1] + dy)
                if (0 <= next_pos[0] < GRID_SIZE and 
                    0 <= next_pos[1] < GRID_SIZE and
                    next_pos not in visited and
                    next_pos not in self.snake and
                    next_pos not in self.obstacles and
                    next_pos != new_obstacle):
                    visited.add(next_pos)
                    queue.append(next_pos)
        
        return False
    
    def move_snake(self) -> None:
        """Move the snake in the current direction"""
        if self.game_over or self.paused:
            return
        
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        # Check wall collision
        if (new_head[0] < 0 or new_head[0] >= GRID_SIZE or 
            new_head[1] < 0 or new_head[1] >= GRID_SIZE):
            self.game_over = True
            self._play_sound("game_over")
            return
        
        # Check self collision
        if new_head in self.snake:
            self.game_over = True
            self._play_sound("game_over")
            return
        
        # Check obstacle collision
        if new_head in self.obstacles:
            self.game_over = True
            self._play_sound("game_over")
            return
        
        self.snake.appendleft(new_head)
        
        # Check food collision
        food_eaten = False
        if self.food and new_head == self.food.pos:
            self._eat_food()
            food_eaten = True
        
        # Check concurrent food collision
        for i, concurrent_food in enumerate(self.concurrent_foods):
            if new_head == concurrent_food.pos:
                self._eat_concurrent_food(concurrent_food)
                self.concurrent_foods.pop(i)
                food_eaten = True
                break
        
        if not food_eaten:
            self.snake.pop()
    
    def _eat_food(self) -> None:
        """Handle food consumption"""
        if not self.food:
            return
        
        food_type = self.food.type
        
        if food_type == FoodType.NORMAL:
            self.score += 1
            self._play_sound("eat")
        elif food_type == FoodType.GOLDEN:
            self.score += 3
            self._play_sound("golden")
        elif food_type == FoodType.ROTTEN:
            self.score = max(0, self.score - 1)
            self._play_sound("rotten")
            
            # Shrink snake if possible
            if len(self.snake) > GAME_TUNING["min_snake_len"]:
                self.snake.pop()
            
            # When rotten food is eaten, spawn normal and golden food concurrently
            self._spawn_concurrent_food()
            return  # Skip normal food spawning since we handled it above
        
        self.food_eaten += 1
        
        # Update speed with more gradual progression
        if FEATURES["speed_scales_with_eats"]:
            # More gradual speed increase - starts slow, accelerates more slowly
            speed_increase = self.food_eaten * GAME_TUNING["speed_step_per_food"]
            # Add a small bonus for higher scores to make it more challenging
            if self.food_eaten > 10:
                speed_increase += (self.food_eaten - 10) * 0.1
            
            self.speed = min(
                GAME_TUNING["speed_max"],
                GAME_TUNING["speed_base"] + speed_increase
            )
        
        # Spawn new food
        self.spawn_food()
        
        # Spawn obstacles
        if (FEATURES["progressive_obstacles"] and 
            self.food_eaten % GAME_TUNING["obstacle_every_n_foods"] == 0):
            self.spawn_obstacle()
    
    def _play_sound(self, sound_name: str) -> None:
        """Play a sound effect if available"""
        if FEATURES["sound_effects"] and self.sounds.get(sound_name):
            try:
                self.sounds[sound_name].play()
            except Exception:
                pass  # Ignore sound errors
    
    def update_food(self) -> None:
        """Update moving food position"""
        if (self.food and self.food.is_moving and 
            self.tick_count % GAME_TUNING["food_move_every_n_ticks"] == 0):
            
            # Try to move food to adjacent empty cell
            directions = list(DIRECTIONS.values())
            random.shuffle(directions)
            
            for dx, dy in directions:
                new_pos = (self.food.pos[0] + dx, self.food.pos[1] + dy)
                if (0 <= new_pos[0] < GRID_SIZE and 
                    0 <= new_pos[1] < GRID_SIZE and
                    new_pos not in self.snake and 
                    new_pos not in self.obstacles):
                    self.food.pos = new_pos
                    break
    
    def get_snake_color(self, score: int) -> Tuple[int, int, int]:
        """Get snake color based on score tier"""
        if not FEATURES["score_tier_colors"]:
            return GREEN
        
        tiers = GAME_TUNING["score_tiers"]
        colors = GAME_TUNING["tier_colors"]
        
        for i in range(len(tiers) - 1, -1, -1):
            if score >= tiers[i]:
                color_hex = colors[i]
                # Convert hex to RGB
                return tuple(int(color_hex[j:j+2], 16) for j in (1, 3, 5))
        
        return GREEN  # Default color
    
    def _draw_animated_background(self) -> None:
        """Draw animated gradient background"""
        self.background_phase += 0.01
        
        # Create gradient colors that shift over time
        phase = self.background_phase % (2 * math.pi)
        
        # Color transitions: blue -> purple -> pink -> back to blue
        r = int(128 + 127 * math.sin(phase))
        g = int(64 + 64 * math.sin(phase + 2 * math.pi / 3))
        b = int(192 + 63 * math.sin(phase + 4 * math.pi / 3))
        
        # Create gradient surface
        gradient_surface = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
        
        # Draw vertical gradient
        for y in range(WINDOW_SIZE):
            # Add some variation based on y position
            intensity = 0.7 + 0.3 * math.sin(y * 0.01 + phase)
            color = (
                int(r * intensity),
                int(g * intensity),
                int(b * intensity)
            )
            pygame.draw.line(gradient_surface, color, (0, y), (WINDOW_SIZE, y))
        
        self.screen.blit(gradient_surface, (0, 0))
        
        # Grid lines removed as requested
    
    def _draw_snake_head(self, head_pos: Tuple[int, int], direction: Tuple[int, int], color: Tuple[int, int, int]) -> None:
        """Draw snake head with eyes and tongue"""
        x, y = head_pos
        cell_size = GAME_TUNING["grid_cell"]
        
        # Calculate head center
        center_x = x * cell_size + cell_size // 2
        center_y = y * cell_size + cell_size // 2
        
        # Draw head body (slightly larger than body segments)
        head_rect = pygame.Rect(
            x * cell_size + 2,
            y * cell_size + 2,
            cell_size - 4,
            cell_size - 4
        )
        pygame.draw.rect(self.screen, color, head_rect)
        
        # Calculate rotation angle based on direction
        if direction == DIRECTIONS["RIGHT"]:
            angle = 0
        elif direction == DIRECTIONS["DOWN"]:
            angle = 90
        elif direction == DIRECTIONS["LEFT"]:
            angle = 180
        else:  # UP
            angle = 270
        
        # Draw eyes
        eye_offset = cell_size // 4
        eye_size = 3
        
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
        
        # Draw tongue (flicking in and out)
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
            # Fork
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
            concurrent_text = self.small_font.render(f"Golden Foods: {len(self.concurrent_foods)}", True, WHITE)
            self.screen.blit(concurrent_text, (10, 80))
        
        # Draw pause indicator
        if self.paused:
            pause_text = self.font.render("PAUSED", True, WHITE)
            text_rect = pause_text.get_rect(center=(WINDOW_SIZE//2, WINDOW_SIZE//2))
            self.screen.blit(pause_text, text_rect)
        
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
