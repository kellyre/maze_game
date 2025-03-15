import pygame
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple, Set, Optional

# Constants
WALL_WIDTH = 3
PATH_WIDTH = 12
DOT_SIZE = 8
MAZE_SIZE = 40  # Number of cells in each dimension
BACKGROUND_COLOR = (240, 240, 255)  # Very pale blue
WALL_COLOR = (0, 0, 0)  # Black
PLAYER_COLOR = (0, 0, 180)  # Dark blue
GOAL_COLOR = (0, 180, 0)  # Green
WINDOW_TITLE = "Maze Game"

class Direction(Enum):
    UP = (0, -1)
    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)

@dataclass
class Cell:
    x: int
    y: int
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        if not isinstance(other, Cell):
            return False
        return self.x == other.x and self.y == other.y
    
    def get_neighbor(self, direction: Direction) -> 'Cell':
        dx, dy = direction.value
        return Cell(self.x + dx, self.y + dy)

class MazeGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.walls = set()  # Set of walls (cell1, cell2)
        self.init_walls()
        
    def init_walls(self):
        # Initialize all walls
        for y in range(self.height):
            for x in range(self.width):
                cell = Cell(x, y)
                # Add walls to the right and down
                if x < self.width - 1:
                    self.walls.add((cell, cell.get_neighbor(Direction.RIGHT)))
                if y < self.height - 1:
                    self.walls.add((cell, cell.get_neighbor(Direction.DOWN)))
    
    def generate_maze(self) -> Set[Tuple[Cell, Cell]]:
        """Generate a maze using randomized Prim's algorithm"""
        # Start with a grid full of walls
        visited_cells = set()
        frontier = set()
        
        # Start with the top-left cell
        start_cell = Cell(0, 0)
        visited_cells.add(start_cell)
        
        # Add unvisited neighbors to frontier
        self._add_frontier_cells(start_cell, visited_cells, frontier)
        
        # While there are cells in the frontier
        while frontier:
            # Pick a random frontier cell
            current = random.choice(list(frontier))
            frontier.remove(current)
            
            # Find neighbors that are already in the maze
            neighbors = []
            for direction in Direction:
                neighbor = current.get_neighbor(direction)
                if 0 <= neighbor.x < self.width and 0 <= neighbor.y < self.height:
                    if neighbor in visited_cells:
                        neighbors.append(neighbor)
            
            if neighbors:
                # Connect to a random neighbor by removing the wall between them
                neighbor = random.choice(neighbors)
                self._remove_wall(current, neighbor)
                
                # Add the current cell to the maze
                visited_cells.add(current)
                
                # Add unvisited neighbors to frontier
                self._add_frontier_cells(current, visited_cells, frontier)
        
        # Ensure there's a path from start to goal
        self._ensure_path_exists(Cell(0, 0), Cell(self.width-1, self.height-1))
        
        return self.walls
    
    def _add_frontier_cells(self, cell: Cell, visited: set, frontier: set):
        """Add unvisited neighbors to the frontier"""
        for direction in Direction:
            neighbor = cell.get_neighbor(direction)
            if 0 <= neighbor.x < self.width and 0 <= neighbor.y < self.height:
                if neighbor not in visited and neighbor not in frontier:
                    frontier.add(neighbor)
    
    def _remove_wall(self, cell1: Cell, cell2: Cell):
        """Remove the wall between two cells"""
        if cell1.x > cell2.x or cell1.y > cell2.y:
            cell1, cell2 = cell2, cell1
        if (cell1, cell2) in self.walls:
            self.walls.remove((cell1, cell2))
    
    def _ensure_path_exists(self, start: Cell, end: Cell):
        """Make sure there's a path from start to end"""
        # Use BFS to check if a path exists
        if not self._has_path(start, end):
            # If no path exists, create one
            self._create_path(start, end)
    
    def _has_path(self, start: Cell, end: Cell) -> bool:
        """Check if there's a path from start to end using BFS"""
        visited = set()
        queue = [start]
        visited.add(start)
        
        while queue:
            current = queue.pop(0)
            if current == end:
                return True
            
            for direction in Direction:
                neighbor = current.get_neighbor(direction)
                if 0 <= neighbor.x < self.width and 0 <= neighbor.y < self.height:
                    if neighbor not in visited and not self.is_wall_between(current, neighbor):
                        visited.add(neighbor)
                        queue.append(neighbor)
        
        return False
    
    def _create_path(self, start: Cell, end: Cell):
        """Create a path from start to end by removing walls"""
        current = start
        visited = {start}
        path = [start]
        
        # Simple algorithm to move toward the goal
        while current != end:
            next_cell = None
            # Try to move toward the goal
            if current.x < end.x:
                next_cell = current.get_neighbor(Direction.RIGHT)
            elif current.x > end.x:
                next_cell = current.get_neighbor(Direction.LEFT)
            elif current.y < end.y:
                next_cell = current.get_neighbor(Direction.DOWN)
            else:
                next_cell = current.get_neighbor(Direction.UP)
            
            # If we can't move toward the goal, try other directions
            if not (0 <= next_cell.x < self.width and 0 <= next_cell.y < self.height) or next_cell in visited:
                for direction in Direction:
                    candidate = current.get_neighbor(direction)
                    if 0 <= candidate.x < self.width and 0 <= candidate.y < self.height and candidate not in visited:
                        next_cell = candidate
                        break
            
            if next_cell and 0 <= next_cell.x < self.width and 0 <= next_cell.y < self.height:
                self._remove_wall(current, next_cell)
                visited.add(next_cell)
                path.append(next_cell)
                current = next_cell
            else:
                # Backtrack if stuck
                path.pop()
                if not path:
                    break
                current = path[-1]
    
    def is_wall_between(self, cell1: Cell, cell2: Cell) -> bool:
        """Check if there's a wall between two adjacent cells"""
        if cell1.x > cell2.x or (cell1.x == cell2.x and cell1.y > cell2.y):
            cell1, cell2 = cell2, cell1
        return (cell1, cell2) in self.walls

class MazeGame:
    def __init__(self):
        pygame.init()
        # Disable default key repeat and implement our own
        pygame.key.set_repeat(0)  # Disable built-in key repeat
        
        self.cell_size = PATH_WIDTH + WALL_WIDTH
        self.screen_width = MAZE_SIZE * self.cell_size + WALL_WIDTH
        self.screen_height = MAZE_SIZE * self.cell_size + WALL_WIDTH
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(WINDOW_TITLE)
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.start_time = 0
        self.elapsed_time = 0
        
        # Movement timing control
        self.key_held_time = 0
        self.initial_delay = 500  # Wait 500ms before starting to repeat
        self.repeat_delay = 250   # Then move every 250ms
        self.last_move_time = 0
        self.last_key = None
        
        self.maze_generator = MazeGenerator(MAZE_SIZE, MAZE_SIZE)
        self.walls = self.maze_generator.generate_maze()
        
        # Player and goal positions (in grid coordinates)
        self.player_pos = Cell(0, 0)
        self.goal_pos = Cell(MAZE_SIZE - 1, MAZE_SIZE - 1)
        
        # Font for text
        self.font = pygame.font.SysFont(None, 36)
    
    def cell_to_pixel(self, cell: Cell) -> Tuple[int, int]:
        """Convert cell coordinates to pixel coordinates (center of cell)"""
        x = cell.x * self.cell_size + WALL_WIDTH + PATH_WIDTH // 2
        y = cell.y * self.cell_size + WALL_WIDTH + PATH_WIDTH // 2
        return (x, y)
    
    def is_wall_between(self, cell1: Cell, cell2: Cell) -> bool:
        """Check if there's a wall between two adjacent cells"""
        if cell1.x > cell2.x or (cell1.x == cell2.x and cell1.y > cell2.y):
            cell1, cell2 = cell2, cell1
        return (cell1, cell2) in self.walls
    
    def can_move(self, from_cell: Cell, to_cell: Cell) -> bool:
        """Check if player can move from one cell to another"""
        # Check if the destination is within bounds
        if not (0 <= to_cell.x < MAZE_SIZE and 0 <= to_cell.y < MAZE_SIZE):
            return False
        
        # Check if there's a wall between the cells
        dx = to_cell.x - from_cell.x
        dy = to_cell.y - from_cell.y
        
        # For diagonal movement, check both orthogonal paths
        if dx != 0 and dy != 0:
            # Check if both orthogonal paths are clear
            return (not self.is_wall_between(from_cell, Cell(from_cell.x + dx, from_cell.y)) and
                    not self.is_wall_between(Cell(from_cell.x + dx, from_cell.y), to_cell) and
                    not self.is_wall_between(from_cell, Cell(from_cell.x, from_cell.y + dy)) and
                    not self.is_wall_between(Cell(from_cell.x, from_cell.y + dy), to_cell))
        
        # For orthogonal movement
        return not self.is_wall_between(from_cell, to_cell)
    
    def draw_maze(self):
        """Draw the maze, player, and goal"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw walls
        for wall in self.walls:
            cell1, cell2 = wall
            x1, y1 = self.cell_to_pixel(cell1)
            x2, y2 = self.cell_to_pixel(cell2)
            
            # Determine wall position
            if cell1.x == cell2.x:  # Horizontal wall
                pygame.draw.line(self.screen, WALL_COLOR, 
                                (x1 - PATH_WIDTH//2, y1 + PATH_WIDTH//2), 
                                (x1 + PATH_WIDTH//2, y1 + PATH_WIDTH//2), 
                                WALL_WIDTH)
            else:  # Vertical wall
                pygame.draw.line(self.screen, WALL_COLOR, 
                                (x1 + PATH_WIDTH//2, y1 - PATH_WIDTH//2), 
                                (x1 + PATH_WIDTH//2, y1 + PATH_WIDTH//2), 
                                WALL_WIDTH)
        
        # Draw wall intersections (corners)
        for y in range(MAZE_SIZE):
            for x in range(MAZE_SIZE):
                cell = Cell(x, y)
                # Check if this cell has walls in multiple directions
                has_right_wall = x < MAZE_SIZE-1 and (cell, cell.get_neighbor(Direction.RIGHT)) in self.walls
                has_down_wall = y < MAZE_SIZE-1 and (cell, cell.get_neighbor(Direction.DOWN)) in self.walls
                
                if has_right_wall and has_down_wall:
                    # Draw a small square at the intersection
                    px, py = self.cell_to_pixel(cell)
                    pygame.draw.rect(self.screen, WALL_COLOR, 
                                    (px + PATH_WIDTH//2 - WALL_WIDTH//2, 
                                     py + PATH_WIDTH//2 - WALL_WIDTH//2,
                                     WALL_WIDTH, WALL_WIDTH))
        
        # Draw outer walls
        pygame.draw.rect(self.screen, WALL_COLOR, (0, 0, self.screen_width, WALL_WIDTH))
        pygame.draw.rect(self.screen, WALL_COLOR, (0, 0, WALL_WIDTH, self.screen_height))
        pygame.draw.rect(self.screen, WALL_COLOR, (0, self.screen_height - WALL_WIDTH, self.screen_width, WALL_WIDTH))
        pygame.draw.rect(self.screen, WALL_COLOR, (self.screen_width - WALL_WIDTH, 0, WALL_WIDTH, self.screen_height))
        
        # Draw player
        player_pixel = self.cell_to_pixel(self.player_pos)
        pygame.draw.circle(self.screen, PLAYER_COLOR, player_pixel, DOT_SIZE)
        
        # Draw goal
        goal_pixel = self.cell_to_pixel(self.goal_pos)
        pygame.draw.circle(self.screen, GOAL_COLOR, goal_pixel, DOT_SIZE)
    
    def show_modal(self):
        """Show modal window with time and options"""
        modal_width, modal_height = 300, 200
        modal_x = (self.screen_width - modal_width) // 2
        modal_y = (self.screen_height - modal_height) // 2
        
        # Draw modal background
        pygame.draw.rect(self.screen, (200, 200, 200), 
                        (modal_x, modal_y, modal_width, modal_height))
        pygame.draw.rect(self.screen, (100, 100, 100), 
                        (modal_x, modal_y, modal_width, modal_height), 2)
        
        # Draw text
        time_text = f"Time: {self.elapsed_time:.2f} seconds"
        time_surface = self.font.render(time_text, True, (0, 0, 0))
        self.screen.blit(time_surface, (modal_x + 50, modal_y + 50))
        
        # Draw buttons
        exit_button = pygame.Rect(modal_x + 50, modal_y + 100, 80, 40)
        new_game_button = pygame.Rect(modal_x + 170, modal_y + 100, 80, 40)
        
        pygame.draw.rect(self.screen, (150, 150, 150), exit_button)
        pygame.draw.rect(self.screen, (150, 150, 150), new_game_button)
        
        exit_text = self.font.render("Exit", True, (0, 0, 0))
        new_game_text = self.font.render("New", True, (0, 0, 0))
        
        self.screen.blit(exit_text, (exit_button.x + 20, exit_button.y + 10))
        self.screen.blit(new_game_text, (new_game_button.x + 20, new_game_button.y + 10))
        
        pygame.display.flip()
        
        # Handle button clicks
        waiting_for_click = True
        while waiting_for_click:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting_for_click = False
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if exit_button.collidepoint(mouse_pos):
                        waiting_for_click = False
                        self.running = False
                    elif new_game_button.collidepoint(mouse_pos):
                        waiting_for_click = False
                        self.reset_game()
    
    def reset_game(self):
        """Reset the game with a new maze"""
        self.maze_generator = MazeGenerator(MAZE_SIZE, MAZE_SIZE)
        self.walls = self.maze_generator.generate_maze()
        self.player_pos = Cell(0, 0)
        self.game_over = False
        self.start_time = time.time()
    
    def handle_movement(self, key):
        """Handle player movement based on key pressed"""
        dx, dy = 0, 0
        if key == pygame.K_UP:
            dy -= 1
        elif key == pygame.K_DOWN:
            dy += 1
        elif key == pygame.K_LEFT:
            dx -= 1
        elif key == pygame.K_RIGHT:
            dx += 1
        
        new_pos = Cell(self.player_pos.x + dx, self.player_pos.y + dy)
        if self.can_move(self.player_pos, new_pos):
            self.player_pos = new_pos

    def run(self):
        """Main game loop"""
        self.start_time = time.time()
        
        while self.running:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    # When a key is first pressed, move immediately
                    if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                        self.last_key = event.key
                        self.key_held_time = 0
                        self.last_move_time = current_time
                        self.handle_movement(event.key)
                elif event.type == pygame.KEYUP:
                    # Reset when key is released
                    if event.key == self.last_key:
                        self.last_key = None
            
            # Handle held keys with custom repeat rate
            if not self.game_over and self.last_key:
                # Calculate time since key was first pressed
                self.key_held_time = current_time - self.last_move_time
                
                # After initial delay, check if we should move again
                if self.key_held_time > self.initial_delay:
                    time_since_last_move = current_time - self.last_move_time
                    if time_since_last_move > self.repeat_delay:
                        self.handle_movement(self.last_key)
                        self.last_move_time = current_time
            
            # Check if player reached the goal
            if self.player_pos == self.goal_pos:
                self.elapsed_time = time.time() - self.start_time
                self.game_over = True
                self.show_modal()
            
            self.draw_maze()
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    game = MazeGame()
    game.run()