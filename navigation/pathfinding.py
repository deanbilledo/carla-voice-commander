"""
A* pathfinding algorithm for navigation
"""

import heapq
import math
import numpy as np
from utils.logger import Logger

class Node:
    """Node for A* pathfinding"""
    
    def __init__(self, position, g_cost=0, h_cost=0, parent=None):
        self.position = position  # (x, y)
        self.g_cost = g_cost  # Cost from start
        self.h_cost = h_cost  # Heuristic cost to goal
        self.f_cost = g_cost + h_cost  # Total cost
        self.parent = parent
    
    def __lt__(self, other):
        return self.f_cost < other.f_cost
    
    def __eq__(self, other):
        return self.position == other.position

class AStarPathfinder:
    """A* pathfinding implementation for CARLA navigation"""
    
    def __init__(self, grid_size=2.0):
        self.logger = Logger.get_logger(__name__)
        self.grid_size = grid_size  # Size of each grid cell in meters
        self.obstacles = set()  # Set of obstacle positions
        
    def add_obstacle(self, position):
        """Add obstacle at position"""
        grid_pos = self._world_to_grid(position)
        self.obstacles.add(grid_pos)
    
    def add_obstacles(self, obstacle_list):
        """Add multiple obstacles"""
        for obstacle in obstacle_list:
            self.add_obstacle(obstacle)
    
    def clear_obstacles(self):
        """Clear all obstacles"""
        self.obstacles.clear()
    
    def find_path(self, start_pos, goal_pos):
        """
        Find path from start to goal using A*
        
        Args:
            start_pos (tuple): Start position (x, y)
            goal_pos (tuple): Goal position (x, y)
            
        Returns:
            list: List of waypoints from start to goal
        """
        try:
            start_grid = self._world_to_grid(start_pos)
            goal_grid = self._world_to_grid(goal_pos)
            
            # Initialize start node
            start_node = Node(start_grid, 0, self._heuristic(start_grid, goal_grid))
            
            # Open and closed sets
            open_set = [start_node]
            closed_set = set()
            
            while open_set:
                # Get node with lowest f_cost
                current_node = heapq.heappop(open_set)
                
                # Check if goal reached
                if current_node.position == goal_grid:
                    path = self._reconstruct_path(current_node)
                    return self._grid_to_world_path(path)
                
                closed_set.add(current_node.position)
                
                # Check neighbors
                for neighbor_pos in self._get_neighbors(current_node.position):
                    # Skip if obstacle or already processed
                    if neighbor_pos in self.obstacles or neighbor_pos in closed_set:
                        continue
                    
                    # Calculate costs
                    g_cost = current_node.g_cost + self._distance(current_node.position, neighbor_pos)
                    h_cost = self._heuristic(neighbor_pos, goal_grid)
                    
                    # Create neighbor node
                    neighbor_node = Node(neighbor_pos, g_cost, h_cost, current_node)
                    
                    # Check if this path is better
                    existing_node = self._find_node_in_open_set(open_set, neighbor_pos)
                    if existing_node is None:
                        heapq.heappush(open_set, neighbor_node)
                    elif g_cost < existing_node.g_cost:
                        existing_node.g_cost = g_cost
                        existing_node.f_cost = g_cost + h_cost
                        existing_node.parent = current_node
            
            self.logger.warning("No path found")
            return []
            
        except Exception as e:
            self.logger.error(f"Error in pathfinding: {e}")
            return []
    
    def _world_to_grid(self, world_pos):
        """Convert world coordinates to grid coordinates"""
        return (int(world_pos[0] / self.grid_size), int(world_pos[1] / self.grid_size))
    
    def _grid_to_world(self, grid_pos):
        """Convert grid coordinates to world coordinates"""
        return (grid_pos[0] * self.grid_size, grid_pos[1] * self.grid_size)
    
    def _grid_to_world_path(self, grid_path):
        """Convert grid path to world path"""
        return [{"x": pos[0] * self.grid_size, "y": pos[1] * self.grid_size} 
                for pos in grid_path]
    
    def _get_neighbors(self, position):
        """Get neighboring grid positions"""
        x, y = position
        neighbors = []
        
        # 8-directional movement
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                neighbors.append((x + dx, y + dy))
        
        return neighbors
    
    def _distance(self, pos1, pos2):
        """Calculate Euclidean distance between positions"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def _heuristic(self, pos1, pos2):
        """Heuristic function (Euclidean distance)"""
        return self._distance(pos1, pos2)
    
    def _reconstruct_path(self, node):
        """Reconstruct path from goal node to start"""
        path = []
        current = node
        
        while current:
            path.append(current.position)
            current = current.parent
        
        return path[::-1]  # Reverse to get start-to-goal path
    
    def _find_node_in_open_set(self, open_set, position):
        """Find node with given position in open set"""
        for node in open_set:
            if node.position == position:
                return node
        return None
    
    def smooth_path(self, path, iterations=3):
        """Smooth path using simple averaging"""
        if len(path) < 3:
            return path
        
        smoothed = path.copy()
        
        for _ in range(iterations):
            new_path = [smoothed[0]]  # Keep start point
            
            for i in range(1, len(smoothed) - 1):
                # Average with neighbors
                prev_point = smoothed[i - 1]
                curr_point = smoothed[i]
                next_point = smoothed[i + 1]
                
                smoothed_x = (prev_point['x'] + curr_point['x'] + next_point['x']) / 3
                smoothed_y = (prev_point['y'] + curr_point['y'] + next_point['y']) / 3
                
                new_path.append({"x": smoothed_x, "y": smoothed_y})
            
            new_path.append(smoothed[-1])  # Keep end point
            smoothed = new_path
        
        return smoothed

# Example usage
if __name__ == "__main__":
    pathfinder = AStarPathfinder(grid_size=1.0)
    
    # Add some obstacles
    obstacles = [(5, 5), (5, 6), (5, 7), (6, 5), (7, 5)]
    pathfinder.add_obstacles(obstacles)
    
    # Find path
    start = (0, 0)
    goal = (10, 10)
    
    path = pathfinder.find_path(start, goal)
    print(f"Path found: {len(path)} waypoints")
    for i, waypoint in enumerate(path):
        print(f"  {i}: ({waypoint['x']}, {waypoint['y']})")
    
    # Smooth path
    smoothed_path = pathfinder.smooth_path(path)
    print(f"Smoothed path: {len(smoothed_path)} waypoints")
