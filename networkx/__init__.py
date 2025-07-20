class DiGraph:
    def __init__(self):
        self._succ = {}
        self.nodes = {}

    def add_node(self, n, **attrs):
        self.nodes.setdefault(n, {}).update(attrs)
        self._succ.setdefault(n, set())

    def __contains__(self, n):
        return n in self._succ

    def add_edge(self, u, v):
        self.add_node(u)
        self.add_node(v)
        self._succ[u].add(v)


def is_directed_acyclic_graph(g: DiGraph) -> bool:
    visited = set()
    stack = set()

    def dfs(node):
        if node in stack:
            return False
        if node in visited:
            return True
        stack.add(node)
        for nbr in g._succ.get(node, []):
            if not dfs(nbr):
                return False
        stack.remove(node)
        visited.add(node)
        return True

    return all(dfs(n) for n in list(g._succ))


def topological_sort(g: DiGraph):
    visited = set()
    order = []

    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        for nbr in g._succ.get(node, []):
            dfs(nbr)
        order.append(node)

    for n in list(g._succ):
        dfs(n)

    return order
