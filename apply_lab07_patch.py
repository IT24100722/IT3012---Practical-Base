import sys

src = open('agent.py').read()
if 'KnowledgeBase' in src:
    sys.exit("agent.py already contains KnowledgeBase - patch not applied again.")

edits = [
    ("import math\n",
     "import math\nfrom logic_engine import KnowledgeBase\n"),

    ("        self.nodes_expanded = 0        # how many nodes the last search expanded\n",
     "        self.nodes_expanded = 0        # how many nodes the last search expanded\n"
     "        self.kb = KnowledgeBase()      # Lab 07: declarative knowledge base\n"
     "        self.kb.tell_rule(['TargetVisible', 'HasDust'], 'SafeToEngage')          # Rule 1\n"
     "        self.kb.tell_rule(['SafeToEngage', 'BloodseekerMissing'], 'Retreat')     # Rule 2\n"),

    ("    # ---------- BFS: FIFO queue ----------\n",
     "    # ---------- Lab 07: feasibility check using the Knowledge Base ----------\n"
     "    def _is_feasible(self, tile, tile_facts):\n"
     "        \"\"\"Reachable is about walls; feasible is about logic. Ask the KB whether Retreat follows.\"\"\"\n"
     "        self.kb.clear_facts()\n"
     "        for fact in tile_facts.get(tile, []):\n"
     "            self.kb.tell_fact(fact)\n"
     "        self.kb.forward_chain()\n"
     "        return 'Retreat' not in self.kb.facts\n\n"
     "    # ---------- BFS: FIFO queue ----------\n"),

    ("def astar_search(self, start_pos, goal_pos, walls, grid_size, heuristic_type='manhattan'):\n",
     "def astar_search(self, start_pos, goal_pos, walls, grid_size, heuristic_type='manhattan', tile_facts=None):\n"
     "        tile_facts = tile_facts or {}                  # None is treated as {}\n"),

    ("                if nxt not in reached_states:\n"
     "                    g_new = g_cost + step_cost\n",
     "                if nxt not in reached_states:\n"
     "                    if not self._is_feasible(nxt, tile_facts):\n"
     "                        continue                       # physically reachable but logically unsafe\n"
     "                    g_new = g_cost + step_cost\n"),

    ("            foods = sorted(",
     "            tile_facts = {\n"
     "                (1, 0): ['TargetVisible', 'HasDust', 'BloodseekerMissing'],  # deduces Retreat: blocked\n"
     "                (0, 1): ['TargetVisible', 'HasDust'],                        # SafeToEngage only: allowed\n"
     "            }\n"
     "            foods = sorted("),
    ("self.astar_search(start, goal, walls, grid_size, heuristic_type='manhattan')",
     "self.astar_search(start, goal, walls, grid_size, heuristic_type='manhattan',\n"
     "                                             tile_facts=tile_facts)"),
]

for old, new in edits:
    if src.count(old) != 1:
        sys.exit("Could not find a unique place for this edit, nothing was changed:\n" + old)
    src = src.replace(old, new)

open('agent.py', 'w').write(src)
print("agent.py patched for Lab 07.")
