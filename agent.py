# agent.py
class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        # If standing directly on food, or just wander / move towards coordinates
        pos = percept['agent_pos']
        # Simple heuristic or fallback random sweep
        return random.choice(self.actions_pool)

# ---------------- Labs 03 and 04: search agent ----------------
from collections import deque
import heapq
import math

# Moves the search can use: action name -> (dx, dy)
SEARCH_MOVES = [('Up', (0, 1)), ('Down', (0, -1)), ('Left', (-1, 0)), ('Right', (1, 0))]


class SearchAgent:
    """Goal-based planning agent: searches the state space offline, then executes the plan."""

    def __init__(self, algo='BFS'):
        self.plan = []                 # sequence of actions still to execute
        self.active_algo = algo        # 'BFS', 'DFS', 'UCS' or 'AStar'
        self.nodes_expanded = 0        # how many nodes the last search expanded

    # ---------- Step 1.1: heuristic functions ----------
    def manhattan_distance(self, pos, goal):
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def euclidean_distance(self, pos, goal):
        return math.sqrt((pos[0] - goal[0]) ** 2 + (pos[1] - goal[1]) ** 2)

    # ---------- shared helpers ----------
    def _neighbors(self, state, walls, grid_size):
        """Successor function: yields (action, next_state, step_cost) for every legal move."""
        width, height = grid_size
        for action, (dx, dy) in SEARCH_MOVES:
            nx, ny = state[0] + dx, state[1] + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in walls:
                yield action, (nx, ny), 1          # uniform step cost of 1

    def _build_plan(self, parent, goal):
        """Walk back from the goal through the parent links to rebuild the action list."""
        actions = []
        state = goal
        while parent[state] is not None:
            state, action = parent[state]
            actions.append(action)
        actions.reverse()
        return actions

    # ---------- BFS: FIFO queue ----------
    def bfs_search(self, start, goal, walls, grid_size):
        frontier = deque([start])
        reached = {start}
        parent = {start: None}
        while frontier:
            state = frontier.popleft()                 # FIFO: shallowest node first
            self.nodes_expanded += 1
            if state == goal:
                return self._build_plan(parent, goal)
            for action, nxt, _ in self._neighbors(state, walls, grid_size):
                if nxt not in reached:
                    reached.add(nxt)
                    parent[nxt] = (state, action)
                    frontier.append(nxt)
        return None

    # ---------- DFS: LIFO stack ----------
    def dfs_search(self, start, goal, walls, grid_size):
        frontier = [start]
        reached = {start}
        parent = {start: None}
        while frontier:
            state = frontier.pop()                     # LIFO: deepest node first
            self.nodes_expanded += 1
            if state == goal:
                return self._build_plan(parent, goal)
            for action, nxt, _ in self._neighbors(state, walls, grid_size):
                if nxt not in reached:
                    reached.add(nxt)
                    parent[nxt] = (state, action)
                    frontier.append(nxt)
        return None

    # ---------- UCS: priority queue ordered by g(n) ----------
    def ucs_search(self, start, goal, walls, grid_size):
        frontier = [(0, 0, start)]                     # (g, tie-breaker, state)
        best_cost = {start: 0}
        parent = {start: None}
        counter = 0
        while frontier:
            g, _, state = heapq.heappop(frontier)      # lowest path cost first
            if g > best_cost[state]:
                continue                               # stale entry, a cheaper path was found
            self.nodes_expanded += 1
            if state == goal:
                return self._build_plan(parent, goal)
            for action, nxt, cost in self._neighbors(state, walls, grid_size):
                new_g = g + cost
                if nxt not in best_cost or new_g < best_cost[nxt]:
                    best_cost[nxt] = new_g
                    parent[nxt] = (state, action)
                    counter += 1
                    heapq.heappush(frontier, (new_g, counter, nxt))
        return None

    # ---------- Step 1.2: A* search, ordered by f(n) = g(n) + h(n) ----------
    def astar_search(self, start_pos, goal_pos, walls, grid_size, heuristic_type='manhattan'):
        h = self.manhattan_distance if heuristic_type == 'manhattan' else self.euclidean_distance

        frontier = []                                  # priority queue (heap)
        reached_states = set()
        g_start = 0
        f_start = g_start + h(start_pos, goal_pos)
        heapq.heappush(frontier, (f_start, g_start, start_pos, []))   # (f_cost, g_cost, current_pos, path_taken)

        while frontier:
            f_cost, g_cost, current_pos, path_taken = heapq.heappop(frontier)   # lowest f first
            if current_pos in reached_states:
                continue                               # already expanded via a cheaper/equal route
            self.nodes_expanded += 1
            if current_pos == goal_pos:
                return path_taken
            reached_states.add(current_pos)

            for action, nxt, step_cost in self._neighbors(current_pos, walls, grid_size):
                if nxt not in reached_states:
                    g_new = g_cost + step_cost
                    h_new = h(nxt, goal_pos)
                    f_new = g_new + h_new
                    heapq.heappush(frontier, (f_new, g_new, nxt, path_taken + [action]))
        return None

    # ---------- Step 1.3: agent program ----------
    def sense_and_act(self, percept):
        if not self.plan:
            start = tuple(percept['agent_pos'])
            walls = set(map(tuple, percept['walls']))
            grid_size = percept['grid_size']
            foods = sorted(map(tuple, percept['all_food']),
                           key=lambda f: self.manhattan_distance(start, f))   # closest food first

            for goal in foods:
                self.nodes_expanded = 0
                if self.active_algo == 'BFS':
                    path = self.bfs_search(start, goal, walls, grid_size)
                elif self.active_algo == 'DFS':
                    path = self.dfs_search(start, goal, walls, grid_size)
                elif self.active_algo == 'UCS':
                    path = self.ucs_search(start, goal, walls, grid_size)
                elif self.active_algo == 'AStar':
                    path = self.astar_search(start, goal, walls, grid_size, heuristic_type='manhattan')
                else:
                    path = None
                if path is not None:
                    print(f"{self.active_algo}: target {goal}, plan length {len(path)}, "
                          f"nodes expanded {self.nodes_expanded}")
                    self.plan = path + ['suck']        # walk to the food, then eat it
                    break
            if not self.plan:
                return 'Stay'                          # nothing reachable
        return self.plan.pop(0)


# Testing checkpoint (Step 1.1): run  python3 agent.py  to see Manhattan = 7 and Euclidean = 5.0
if __name__ == "__main__":
    agent = SearchAgent()
    print("Manhattan:", agent.manhattan_distance((0, 0), (3, 4)))
    print("Euclidean:", agent.euclidean_distance((0, 0), (3, 4)))
