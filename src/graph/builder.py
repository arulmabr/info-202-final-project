import networkx as nx
from ..storage import Package, Dependency


def build_graph(packages: list[Package], dependencies: list[Dependency]) -> nx.MultiDiGraph:
    """Build a NetworkX MultiDiGraph from packages and dependencies."""
    G = nx.MultiDiGraph()

    # add all packages as nodes
    for pkg in packages:
        G.add_node(pkg.name, **pkg.to_dict())

    # add dependencies as edges
    for dep in dependencies:
        # ensure both nodes exist (add missing ones with minimal info)
        if dep.source not in G:
            G.add_node(dep.source, name=dep.source)
        if dep.target not in G:
            G.add_node(dep.target, name=dep.target)

        G.add_edge(
            dep.source,
            dep.target,
            relation_type=dep.relation_type.value,
            version_constraint=dep.version_constraint,
            source_file=dep.source_file
        )

    return G


def filter_graph(G: nx.MultiDiGraph,
                 domains: list[str] = None,
                 roles: list[str] = None,
                 relation_types: list[str] = None,
                 min_in_degree: int = 0) -> nx.MultiDiGraph:
    """Create a filtered subgraph."""
    nodes_to_keep = set()

    for node, data in G.nodes(data=True):
        if domains and data.get('domain') not in domains:
            continue
        if roles and data.get('role') not in roles:
            continue
        if G.in_degree(node) < min_in_degree:
            continue
        nodes_to_keep.add(node)

    subgraph = G.subgraph(nodes_to_keep).copy()

    # filter edges by relation type
    if relation_types:
        edges_to_remove = []
        for u, v, key, data in subgraph.edges(keys=True, data=True):
            if data.get('relation_type') not in relation_types:
                edges_to_remove.append((u, v, key))
        for u, v, key in edges_to_remove:
            subgraph.remove_edge(u, v, key)

    return subgraph


def get_subgraph_around(G: nx.MultiDiGraph, center: str, depth: int = 2) -> nx.MultiDiGraph:
    """Get a subgraph centered around a specific node."""
    if center not in G:
        return nx.MultiDiGraph()

    nodes = {center}
    frontier = {center}

    for _ in range(depth):
        new_frontier = set()
        for node in frontier:
            # predecessors and successors
            new_frontier.update(G.predecessors(node))
            new_frontier.update(G.successors(node))
        nodes.update(new_frontier)
        frontier = new_frontier

    return G.subgraph(nodes).copy()
