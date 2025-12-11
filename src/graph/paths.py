import networkx as nx


def find_shortest_path(G: nx.MultiDiGraph, source: str, target: str) -> list[str] | None:
    """Find shortest path between two packages."""
    if source not in G or target not in G:
        return None

    try:
        return nx.shortest_path(G, source, target)
    except nx.NetworkXNoPath:
        return None


def find_all_paths(G: nx.MultiDiGraph, source: str, target: str, max_length: int = 5) -> list[list[str]]:
    """Find all paths up to a maximum length."""
    if source not in G or target not in G:
        return []

    try:
        paths = list(nx.all_simple_paths(G, source, target, cutoff=max_length))
        return sorted(paths, key=len)
    except nx.NetworkXNoPath:
        return []


def get_path_details(G: nx.MultiDiGraph, path: list[str]) -> list[dict]:
    """Get detailed information about each step in a path."""
    details = []

    for i, node in enumerate(path):
        node_data = dict(G.nodes[node])
        step = {
            'package': node,
            'domain': node_data.get('domain', 'unknown'),
            'role': node_data.get('role', 'unknown'),
        }

        # add edge info if not the last node
        if i < len(path) - 1:
            next_node = path[i + 1]
            edge_data = G.get_edge_data(node, next_node)
            if edge_data:
                # get first edge (in case of multi-edges)
                first_edge = list(edge_data.values())[0]
                step['edge_type'] = first_edge.get('relation_type')
                step['version'] = first_edge.get('version_constraint')

        details.append(step)

    return details


def find_common_dependencies(G: nx.MultiDiGraph, packages: list[str]) -> list[str]:
    """Find packages that all given packages depend on."""
    if not packages:
        return []

    dep_sets = []
    for pkg in packages:
        if pkg in G:
            deps = set(G.successors(pkg))
            dep_sets.append(deps)

    if not dep_sets:
        return []

    common = dep_sets[0]
    for s in dep_sets[1:]:
        common &= s

    return sorted(common)


def find_common_dependents(G: nx.MultiDiGraph, packages: list[str]) -> list[str]:
    """Find packages that depend on all given packages."""
    if not packages:
        return []

    dependent_sets = []
    for pkg in packages:
        if pkg in G:
            dependents = set(G.predecessors(pkg))
            dependent_sets.append(dependents)

    if not dependent_sets:
        return []

    common = dependent_sets[0]
    for s in dependent_sets[1:]:
        common &= s

    return sorted(common)
