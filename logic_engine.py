# logic_engine.py  (Lab 07: Knowledge Base + Forward Chaining)


class KnowledgeBase:
    """Declarative knowledge base that stores facts and Horn-clause rules."""

    def __init__(self):
        self.facts = set()     # unique string facts, e.g. "TargetVisible"
        self.rules = []        # list of tuples: ([premises], "conclusion")

    def tell_fact(self, fact_string):
        self.facts.add(fact_string)

    def tell_rule(self, premise_list, conclusion_string):
        self.rules.append((list(premise_list), conclusion_string))

    def clear_facts(self):
        self.facts.clear()

    def forward_chain(self):
        """Data-driven inference: keep applying rules until no new fact is deduced."""
        new_facts_added = True
        while new_facts_added:
            new_facts_added = False
            for premises, conclusion in self.rules:
                if conclusion not in self.facts:
                    # Modus Ponens check: if ALL premises are known facts, the conclusion follows
                    if all(p in self.facts for p in premises):
                        self.facts.add(conclusion)
                        new_facts_added = True
