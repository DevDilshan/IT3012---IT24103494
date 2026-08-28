# agent.py
import heapq
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
    """Problem-solving agent that plans paths with uninformed search."""

    DIRECTIONS = {
        'Up': (0, 1),
        'Down': (0, -1),
        'Left': (-1, 0),
        'Right': (1, 0),
    }

    def __init__(self):
        self.plan = []
        self.active_algo = 'BFS'

    def _neighbors(self, pos, walls, grid_size):
        width, height = grid_size
        walls = set(walls)
        x, y = pos

        for action, (dx, dy) in self.DIRECTIONS.items():
            next_pos = (x + dx, y + dy)
            nx, ny = next_pos
            if (
                0 <= nx < width
                and 0 <= ny < height
                and next_pos not in walls
            ):
                yield next_pos, action

    def bfs_search(self, start_pos, goal_pos, walls, grid_size):
        """FIFO frontier — explores shallowest nodes first."""
        start_pos = tuple(start_pos)
        goal_pos = tuple(goal_pos)
        queue = deque([(start_pos, [])])
        reached = {start_pos}

        while queue:
            pos, path = queue.popleft()
            if pos == goal_pos:
                return path

            for next_pos, action in self._neighbors(pos, walls, grid_size):
                if next_pos not in reached:
                    reached.add(next_pos)
                    queue.append((next_pos, path + [action]))

        return None

    def dfs_search(self, start_pos, goal_pos, walls, grid_size):
        """LIFO frontier — explores deepest nodes first."""
        start_pos = tuple(start_pos)
        goal_pos = tuple(goal_pos)
        stack = [(start_pos, [])]
        reached = {start_pos}

        while stack:
            pos, path = stack.pop()
            if pos == goal_pos:
                return path

            for next_pos, action in self._neighbors(pos, walls, grid_size):
                if next_pos not in reached:
                    reached.add(next_pos)
                    stack.append((next_pos, path + [action]))

        return None

    def ucs_search(self, start_pos, goal_pos, walls, grid_size):
        """Priority queue ordered by path cost g(n)."""
        start_pos = tuple(start_pos)
        goal_pos = tuple(goal_pos)
        counter = 0
        frontier = [(0, counter, start_pos, [])]
        reached = {start_pos: 0}

        while frontier:
            cost, _, pos, path = heapq.heappop(frontier)
            if pos == goal_pos:
                return path

            if cost > reached.get(pos, float('inf')):
                continue

            for next_pos, action in self._neighbors(pos, walls, grid_size):
                next_cost = cost + 1
                if next_cost < reached.get(next_pos, float('inf')):
                    reached[next_pos] = next_cost
                    counter += 1
                    heapq.heappush(frontier, (next_cost, counter, next_pos, path + [action]))

        return None

    def _closest_food(self, start_pos, food_positions):
        if not food_positions:
            return None
        start = tuple(start_pos)
        return min(
            food_positions,
            key=lambda food: abs(food[0] - start[0]) + abs(food[1] - start[1]),
        )

    def _plan_to_closest_food(self, percept):
        start_pos = tuple(percept['agent_pos'])
        goal_pos = self._closest_food(start_pos, percept.get('all_food', []))
        if goal_pos is None:
            return []

        walls = percept['walls']
        grid_size = percept['grid_size']

        if self.active_algo == 'DFS':
            path = self.dfs_search(start_pos, goal_pos, walls, grid_size)
        elif self.active_algo == 'UCS':
            path = self.ucs_search(start_pos, goal_pos, walls, grid_size)
        else:
            path = self.bfs_search(start_pos, goal_pos, walls, grid_size)

        return path if path else []

    def sense_and_act(self, percept: dict) -> str:
        if not self.plan:
            self.plan = self._plan_to_closest_food(percept)

        if self.plan:
            return self.plan.pop(0)

        return 'Up'
