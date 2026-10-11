# ---------------------------------------------------------------
# ADD TO agent.py  (put the two imports at the very top of the file,
# and paste the class at the bottom of the file)
# ---------------------------------------------------------------
from collections import deque
import heapq

# Moves the search can use: action name -> (dx, dy)
SEARCH_MOVES = [('Up', (0, 1)), ('Down', (0, -1)), ('Left', (-1, 0)), ('Right', (1, 0))]


class SearchAgent:
    """Goal-based planning agent: searches the state space offline, then executes the plan."""

    def __init__(self, algo='BFS'):
        self.plan = []                 # sequence of actions still to execute
        self.active_algo = algo        # 'BFS', 'DFS' or 'UCS'

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

    # ---------- agent program ----------
    def sense_and_act(self, percept):
        if not self.plan:
            start = tuple(percept['agent_pos'])
            walls = set(map(tuple, percept['walls']))
            grid_size = percept['grid_size']
            foods = sorted(map(tuple, percept['all_food']),
                           key=lambda f: abs(f[0] - start[0]) + abs(f[1] - start[1]))   # closest first
            search = {'BFS': self.bfs_search, 'DFS': self.dfs_search, 'UCS': self.ucs_search}[self.active_algo]
            for goal in foods:
                path = search(start, goal, walls, grid_size)
                if path is not None:
                    self.plan = path + ['suck']        # walk to the food, then eat it
                    break
            if not self.plan:
                return 'Stay'                          # nothing reachable
        return self.plan.pop(0)