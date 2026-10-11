# visual_grid_game.py  (Lab 02: Simple Reflex Agent vs Model-Based Agent)
import random
import sys
import tkinter as tk
from collections import deque

from agent import SearchAgent  # Lab 03: BFS / DFS / UCS planning agent

# Facing directions: 0 = Up, 1 = Right, 2 = Down, 3 = Left
DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
# Lab 03: absolute one-cell moves used by the planning agent
MOVES = {'Up': (0, 1), 'Down': (0, -1), 'Left': (-1, 0), 'Right': (1, 0)}


class VisualGridHuntGame:
    """Grid environment. The agent now has a facing direction and only gets LOCAL percepts."""

    def __init__(self, width=10, height=10, num_food=10, num_opponents=2, custom_walls=None, num_traps=5,
                 max_steps=800):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)
        self.facing = 0          # NEW: agent starts facing Up
        self.max_steps = max_steps

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        self.food_positions = set()
        while len(self.food_positions) < num_food:
            pos_tuple = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            if pos_tuple != (0, 0) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        self.toxic_traps = set()
        while len(self.toxic_traps) < num_traps:
            trap_pos = (random.randint(0, self.width - 1), random.randint(0, self.height - 1))
            if trap_pos != (0, 0) and trap_pos not in self.walls and trap_pos not in self.food_positions:
                self.toxic_traps.add(trap_pos)

        self.opponents = []
        while len(self.opponents) < num_opponents:
            op_pos = [random.randint(0, self.width - 1), random.randint(0, self.height - 1)]
            if tuple(op_pos) != (0, 0) and tuple(op_pos) not in self.walls and tuple(op_pos) not in self.food_positions:
                self.opponents.append(op_pos)

        self.score = 0
        self.steps = 0
        self.collision = False

    def cell_ahead(self):
        dx, dy = DIRECTIONS[self.facing]
        return (self.agent_pos[0] + dx, self.agent_pos[1] + dy)

    def is_blocked(self, cell):
        x, y = cell
        return x < 0 or y < 0 or x >= self.width or y >= self.height or cell in self.walls

    def get_percept(self) -> dict:
        """Partially observable: only local booleans, NO global coordinates (agent_pos removed)."""
        return {
            'wall_ahead': self.is_blocked(self.cell_ahead()),
            'food_here': tuple(self.agent_pos) in self.food_positions,
            'smells_toxin': tuple(self.agent_pos) in self.toxic_traps,
            # --- Lab 03: expose the world model so the agent can plan ---
            'agent_pos': list(self.agent_pos),            # start state for the search
            'grid_size': (self.width, self.height),
            'walls': list(self.walls),
            'all_food': list(self.food_positions),
        }

    def execute_action(self, action: str):
        self.steps += 1

        if action == 'turn_left':
            self.facing = (self.facing - 1) % 4
        elif action == 'turn_right':
            self.facing = (self.facing + 1) % 4
        elif action == 'move_forward':
            target = self.cell_ahead()
            if self.is_blocked(target):
                self.score -= 5
            else:
                self.agent_pos = list(target)
                if target in self.toxic_traps:
                    self.score -= 15
        elif action in MOVES:
            dx, dy = MOVES[action]
            target = (self.agent_pos[0] + dx, self.agent_pos[1] + dy)
            if self.is_blocked(target):
                self.score -= 5
            else:
                self.agent_pos = list(target)
                if target in self.toxic_traps:
                    self.score -= 15
        elif action == 'suck':
            if tuple(self.agent_pos) in self.food_positions:
                self.food_positions.remove(tuple(self.agent_pos))
                self.score += 20

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

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= self.max_steps or self.collision


class SimpleReflexAgent:
    """Step 1.2: strictly IF-THEN rules. No __init__, so it has no memory at all."""

    def sense_and_act(self, percept):
        if percept['food_here']:            # Rule 1
            return 'suck'
        if percept['wall_ahead']:           # Rule 2
            return 'turn_left'
        return 'move_forward'               # Rule 3 (ELSE)


class ModelBasedAgent:
    """Step 1.3: keeps an internal model (dead-reckoned position, facing, visited cells, known walls)."""

    def __init__(self):
        self.x, self.y = 0, 0          # relative position (the agent starts at its own origin)
        self.facing = 0                # relative facing, same convention as the environment
        self.visited = {(0, 0)}        # cells the agent has been on
        self.walls = set()             # cells the agent has discovered to be blocked
        self.last_action = None
        self.last_percept = None

    # ---------- helpers ----------
    def _cell_in(self, direction):
        dx, dy = DIRECTIONS[direction]
        return (self.x + dx, self.y + dy)

    def _is_new(self, direction):
        cell = self._cell_in(direction)
        return cell not in self.visited and cell not in self.walls

    def _turn_towards(self, target):
        diff = (target - self.facing) % 4
        if diff == 0:
            return 'move_forward'
        return 'turn_left' if diff == 3 else 'turn_right'

    def _nearest_unexplored_direction(self):
        """Breadth-first search through remembered cells to the nearest unexplored cell."""
        start = (self.x, self.y)
        queue = deque([(start, None)])
        seen = {start}
        while queue:
            cell, first = queue.popleft()
            for d, (dx, dy) in enumerate(DIRECTIONS):
                nxt = (cell[0] + dx, cell[1] + dy)
                if nxt in self.walls:
                    continue
                step = d if first is None else first
                if nxt not in self.visited:
                    return step
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, step))
        return None

    # ---------- state update ----------
    def update_state(self, percept):
        # TRANSITION MODEL: predict how the last action changed the agent's pose
        if self.last_action == 'turn_left':
            self.facing = (self.facing - 1) % 4
        elif self.last_action == 'turn_right':
            self.facing = (self.facing + 1) % 4
        elif (self.last_action == 'move_forward' and self.last_percept is not None
              and not self.last_percept['wall_ahead']):
            self.x, self.y = self._cell_in(self.facing)
        self.visited.add((self.x, self.y))

        # SENSOR MODEL: interpret the new percept and write it into the model
        if percept['wall_ahead']:
            self.walls.add(self._cell_in(self.facing))

    # ---------- agent program ----------
    def sense_and_act(self, percept):
        self.update_state(percept)
        left = (self.facing - 1) % 4
        right = (self.facing + 1) % 4

        if percept['food_here']:                                       # Rule 1
            action = 'suck'
        elif not percept['wall_ahead'] and self._is_new(self.facing):  # Rule 2
            action = 'move_forward'
        elif self._is_new(left):                                       # Rule 3
            action = 'turn_left'
        elif self._is_new(right):                                      # Rule 4
            action = 'turn_right'
        else:                                                          # Rule 5: boxed in, use memory
            target = self._nearest_unexplored_direction()
            action = 'turn_left' if target is None else self._turn_towards(target)

        self.last_action = action
        self.last_percept = percept
        return action


class GridGameGUI:
    """Tkinter wrapper that dynamically scales cell sizes to keep larger grids on screen."""

    def __init__(self, root, agent, width=10, height=10, num_food=12, num_opponents=2, walls=None):
        self.root = root
        self.agent = agent
        self.root.title("IT3012 - Scalable Multi-Agent Grid Hunt")

        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food, num_opponents=num_opponents,
                                      custom_walls=walls)

        max_canvas_dim = 600
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        self.label = tk.Label(root, text="Score: 0 | Steps: 0", font=("Arial", 14))
        self.label.pack(pady=10)

        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop, font=("Arial", 12), bg="#000066",
                             fg="white")
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
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="W", fill="white",
                                            font=("Arial", 8, "bold"))

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#f59e0b",
                                    outline="#d97706")

        for tx, ty in self.env.toxic_traps:
            cx = tx * self.cell_size + self.cell_size / 2
            cy = (self.env.height - 1 - ty) * self.cell_size + self.cell_size / 2
            r = self.cell_size * 0.3
            self.canvas.create_polygon(cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy,
                                       fill="#7e22ce", outline="#581c87")

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6, fill="#990000",
                                         outline="#7a0000")

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7, fill="#000066",
                                outline="#1e3a8a")

        # NEW: white dot showing which way the agent is facing
        dx, dy = DIRECTIONS[self.env.facing]
        cx = x1 + self.cell_size * 0.35 + dx * self.cell_size * 0.25
        cy = y1 + self.cell_size * 0.35 - dy * self.cell_size * 0.25
        r = self.cell_size * 0.08
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="white", outline="white")

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)
                self.env.execute_action(action)

                self.draw_grid()
                self.label.config(text=f"Score: {self.env.score} | Steps: {self.env.steps} | Action: {action}")
                self.root.after(100, step)
            else:
                end_text = f"Collision! Game Over! Final Score: {self.env.score}" if self.env.collision else f"Finished! Final Score: {self.env.score}"
                self.label.config(text=end_text)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
    # Usage:  python3 visual_grid_game.py reflex   (default)
    #         python3 visual_grid_game.py model
    #         python3 visual_grid_game.py BFS | DFS | UCS | AStar   (search agent)
    choice = sys.argv[1] if len(sys.argv) > 1 else "AStar"
    algos = {"BFS": "BFS", "DFS": "DFS", "UCS": "UCS", "ASTAR": "AStar"}
    if choice.upper() in algos:
        agent = SearchAgent(algo=algos[choice.upper()])
    elif choice == "model":
        agent = ModelBasedAgent()
    else:
        agent = SimpleReflexAgent()

    root = tk.Tk()
    app = GridGameGUI(root, agent, width=12, height=12, num_food=15, num_opponents=0)
    root.mainloop()