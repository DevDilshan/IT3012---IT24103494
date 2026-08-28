# agent.py
import random
from collections import deque


class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        return random.choice(self.actions_pool)


class SimpleReflexAgent:
    """Condition-action agent with no memory — reacts only to the current percept."""

    def sense_and_act(self, percept: dict) -> str:
        # IF food_here THEN suck; IF wall_ahead THEN turn_left; ELSE move_forward
        if percept.get('food_here'):
            return 'suck'
        if percept.get('wall_ahead'):
            return 'Left'
        return 'Up'


class ModelBasedAgent:
    """Maintains internal state to escape loops that trap a simple reflex agent."""

    def __init__(self):
        self.visited_cells = set()
        self.last_action = None
        self.last_percept = None

    def sense_and_act(self, percept: dict) -> str:
        percept_key = (percept.get('wall_ahead'), percept.get('food_here'))

        if percept.get('food_here'):
            self.last_percept = percept_key
            self.last_action = 'suck'
            return 'suck'

        if percept.get('wall_ahead'):
            # Query memory: alternate turns when the same wall percept repeats.
            if percept_key == self.last_percept and self.last_action == 'Left':
                action = 'Right'
            elif percept_key == self.last_percept and self.last_action == 'Right':
                action = 'Left'
            else:
                action = 'Left'

            self.last_percept = percept_key
            self.last_action = action
            return action

        self.last_percept = percept_key
        self.last_action = 'Up'
        return 'Up'


class SearchAgent:
    """Problem-solving agent that plans paths with breadth-first search."""

    def bfs_search(self, start_pos, goal_pos, walls, grid_size):
        width, height = grid_size
        walls = set(walls)
        directions = {
            'Up': (0, 1),
            'Down': (0, -1),
            'Left': (-1, 0),
            'Right': (1, 0),
        }

        queue = deque([(start_pos, [])])
        visited = {start_pos}

        while queue:
            (x, y), path = queue.popleft()
            if (x, y) == goal_pos:
                return path

            for action, (dx, dy) in directions.items():
                next_pos = (x + dx, y + dy)
                nx, ny = next_pos
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and next_pos not in walls
                    and next_pos not in visited
                ):
                    visited.add(next_pos)
                    queue.append((next_pos, path + [action]))

        return None
