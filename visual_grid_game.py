# visual_grid_game.py
import random
import tkinter as tk
from agent import SimpleReflexAgent, ModelBasedAgent, SearchAgent

DIRECTIONS = ['Up', 'Right', 'Down', 'Left']
DIRECTION_DELTAS = {
    'Up': (0, 1),
    'Right': (1, 0),
    'Down': (0, -1),
    'Left': (-1, 0),
}


class VisualGridHuntGame:
    """A flexible Pacman-style grid environment with support for configurable opponents and larger scales."""

    def __init__(self, width=10, height=10, num_food=10, num_opponents=2, num_traps=5, custom_walls=None):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]
        self.facing = 'Up'

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos_tuple = (fx, fy)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        self.toxic_traps = set()
        while len(self.toxic_traps) < num_traps:
            tx = random.randint(0, self.width - 1)
            ty = random.randint(0, self.height - 1)
            trap_tuple = (tx, ty)
            if (
                trap_tuple != (0, 0)
                and trap_tuple not in self.walls
                and trap_tuple not in self.food_positions
                and trap_tuple not in self.toxic_traps
            ):
                self.toxic_traps.add(trap_tuple)

        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            if tuple(op_pos) != (0, 0) and tuple(op_pos) not in self.walls and tuple(op_pos) not in self.food_positions:
                self.opponents.append(op_pos)

        self.score = 0
        self.steps = 0
        self.collision = False
        self.absolute_navigation = False

    def _turn_left(self):
        idx = DIRECTIONS.index(self.facing)
        self.facing = DIRECTIONS[(idx - 1) % 4]

    def _turn_right(self):
        idx = DIRECTIONS.index(self.facing)
        self.facing = DIRECTIONS[(idx + 1) % 4]

    def _cell_ahead(self):
        dx, dy = DIRECTION_DELTAS[self.facing]
        return self.agent_pos[0] + dx, self.agent_pos[1] + dy

    def _is_wall_or_boundary(self, x, y):
        return x < 0 or x >= self.width or y < 0 or y >= self.height or (x, y) in self.walls

    def get_percept(self) -> dict:
        """Local percepts plus global world model for search-based agents."""
        ahead_x, ahead_y = self._cell_ahead()
        return {
            'wall_ahead': self._is_wall_or_boundary(ahead_x, ahead_y),
            'food_here': tuple(self.agent_pos) in self.food_positions,
            'agent_pos': list(self.agent_pos),
            'grid_size': (self.width, self.height),
            'walls': list(self.walls),
            'all_food': list(self.food_positions),
        }

    def _move_forward(self):
        ahead_x, ahead_y = self._cell_ahead()
        if not self._is_wall_or_boundary(ahead_x, ahead_y):
            self.agent_pos = [ahead_x, ahead_y]

    def _collect_food(self):
        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.food_positions:
            self.food_positions.remove(tuple_pos)
            self.score += 20

    def _apply_position_effects(self):
        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.toxic_traps:
            self.score -= 15

        for op in self.opponents:
            move = random.choice(['Up', 'Down', 'Left', 'Right', 'Stay'])
            if move == 'Up' and op[1] < self.height - 1:
                op[1] += 1
            elif move == 'Down' and op[1] > 0:
                op[1] -= 1
            elif move == 'Left' and op[0] > 0:
                op[0] -= 1
            elif move == 'Right' and op[0] < self.width - 1:
                op[0] += 1

            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def execute_action(self, action: str):
        self.steps += 1

        if not self.absolute_navigation:
            relative_aliases = {
                'Left': 'turn_left',
                'Right': 'turn_right',
                'Up': 'move_forward',
            }
            action = relative_aliases.get(action, action)

        if action == 'turn_left':
            self._turn_left()
        elif action == 'turn_right':
            self._turn_right()
        elif action == 'move_forward':
            new_pos = list(self.agent_pos)
            ahead_x, ahead_y = self._cell_ahead()
            if self._is_wall_or_boundary(ahead_x, ahead_y):
                self.score -= 5
            else:
                self.agent_pos = [ahead_x, ahead_y]
        elif action == 'suck':
            self._collect_food()
        elif action in DIRECTION_DELTAS:
            new_pos = list(self.agent_pos)
            dx, dy = DIRECTION_DELTAS[action]
            new_pos[0] += dx
            new_pos[1] += dy

            if self._is_wall_or_boundary(new_pos[0], new_pos[1]):
                self.score -= 5
            else:
                self.agent_pos = new_pos
                self.facing = action
                if tuple(self.agent_pos) in self.food_positions:
                    self._collect_food()

        self._apply_position_effects()

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 60 or self.collision


class GridGameGUI:
    """Tkinter wrapper that dynamically scales cell sizes to keep larger grids on screen."""

    def __init__(
        self,
        root,
        width=10,
        height=10,
        num_food=12,
        num_opponents=2,
        num_traps=5,
        walls=None,
        agent_class=SimpleReflexAgent,
    ):
        self.root = root
        self.root.title("IT3012 - Search Algorithms Lab")
        self.agent = agent_class()

        self.env = VisualGridHuntGame(
            width=width,
            height=height,
            num_food=num_food,
            num_opponents=num_opponents,
            num_traps=num_traps,
            custom_walls=walls,
        )
        self.env.absolute_navigation = agent_class is SearchAgent

        max_canvas_dim = 600
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        agent_name = agent_class.__name__
        self.label = tk.Label(
            root,
            text=f"Agent: {agent_name} | Score: 0 | Steps: 0 | Facing: Up",
            font=("Arial", 14),
        )
        self.label.pack(pady=10)

        self.btn = tk.Button(
            root,
            text="Start Simulation",
            command=self.run_loop,
            font=("Arial", 12),
            bg="#000066",
            fg="white",
        )
        self.btn.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#f1f5f9" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(
                        x1 + self.cell_size / 2,
                        y1 + self.cell_size / 2,
                        text="W",
                        fill="white",
                        font=("Arial", 8, "bold"),
                    )

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(
                x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5,
                fill="#f59e0b", outline="#d97706",
            )

        for tx, ty in self.env.toxic_traps:
            cx = tx * self.cell_size + self.cell_size / 2
            cy = (self.env.height - 1 - ty) * self.cell_size + self.cell_size / 2
            half = self.cell_size * 0.3
            points = [cx, cy - half, cx + half, cy, cx, cy + half, cx - half, cy]
            self.canvas.create_polygon(points, fill="#7e22ce", outline="#581c87")

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(
                x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6,
                fill="#990000", outline="#7a0000",
            )

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        cx = x1 + self.cell_size * 0.35
        cy = y1 + self.cell_size * 0.35
        self.canvas.create_oval(
            x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7,
            fill="#000066", outline="#1e3a8a",
        )

        facing_arrows = {
            'Up': (0, -self.cell_size * 0.25),
            'Down': (0, self.cell_size * 0.25),
            'Left': (-self.cell_size * 0.25, 0),
            'Right': (self.cell_size * 0.25, 0),
        }
        dx, dy = facing_arrows[self.env.facing]
        self.canvas.create_line(cx, cy, cx + dx, cy + dy, fill="#60a5fa", width=3, arrow=tk.LAST)

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)
                self.env.execute_action(action)

                self.draw_grid()
                algo = getattr(self.agent, 'active_algo', '')
                algo_text = f" | Algo: {algo}" if algo else ""
                self.label.config(
                    text=(
                        f"Agent: {self.agent.__class__.__name__}{algo_text} | "
                        f"Score: {self.env.score} | Steps: {self.env.steps} | "
                        f"Facing: {self.env.facing} | Action: {action} | "
                        f"Plan left: {len(getattr(self.agent, 'plan', []))}"
                    )
                )
                self.root.after(250, step)
            else:
                end_text = (
                    f"Collision! Game Over! Final Score: {self.env.score}"
                    if self.env.collision
                    else f"Finished! Final Score: {self.env.score}"
                )
                self.label.config(text=end_text)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
    root = tk.Tk()

    # Maze for comparing BFS, DFS, and UCS path shapes
    search_maze_walls = {
        (1, 0), (2, 0), (3, 0), (4, 0),
        (4, 1), (4, 2), (4, 3),
        (1, 3), (2, 3), (3, 3),
    }

    agent_choice = SearchAgent  # Change active_algo inside SearchAgent: 'BFS', 'DFS', 'UCS'
    app = GridGameGUI(
        root,
        width=6,
        height=4,
        num_food=2,
        num_opponents=0,
        num_traps=0,
        walls=search_maze_walls,
        agent_class=agent_choice,
    )
    root.mainloop()
