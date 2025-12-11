import networkx as nx
from ..storage import Package


def compute_metrics(G: nx.MultiDiGraph) -> dict[str, dict]:
    """Compute all centrality metrics for the graph."""
    # convert to simple DiGraph for some algorithms
    simple = nx.DiGraph(G)

    metrics = {}

    # degree metrics
    in_deg = dict(G.in_degree())
    out_deg = dict(G.out_degree())

    # pagerank
    try:
        pagerank = nx.pagerank(simple, alpha=0.85)
    except nx.PowerIterationFailedConvergence:
        pagerank = {n: 0.0 for n in G.nodes()}

    # betweenness (can be slow on large graphs)
    if len(G) < 1000:
        betweenness = nx.betweenness_centrality(simple)
    else:
        # sample for large graphs
        betweenness = nx.betweenness_centrality(simple, k=min(100, len(G)))

    for node in G.nodes():
        metrics[node] = {
            'in_degree': in_deg.get(node, 0),
            'out_degree': out_deg.get(node, 0),
            'pagerank': pagerank.get(node, 0.0),
            'betweenness': betweenness.get(node, 0.0),
        }

    return metrics


def update_package_metrics(packages: list[Package], G: nx.MultiDiGraph) -> list[Package]:
    """Update packages with computed graph metrics."""
    metrics = compute_metrics(G)

    for pkg in packages:
        if pkg.name in metrics:
            m = metrics[pkg.name]
            pkg.in_degree = m['in_degree']
            pkg.out_degree = m['out_degree']
            pkg.pagerank = m['pagerank']
            pkg.betweenness = m['betweenness']

    return packages


def find_hidden_pillars(G: nx.MultiDiGraph, top_n: int = 20) -> list[tuple[str, dict]]:
    """Find high-centrality packages that may be less visible.

    These are packages with high betweenness/pagerank but potentially
    lower star counts - the "hidden pillars" of the ecosystem.
    """
    metrics = compute_metrics(G)

    # rank by composite score
    scored = []
    for node, m in metrics.items():
        data = G.nodes[node]
        stars = data.get('github_stars') or 0

        # high centrality, lower visibility = hidden pillar
        centrality_score = m['pagerank'] * 1000 + m['betweenness'] * 100
        visibility_penalty = min(stars / 10000, 1.0)  # cap penalty
        score = centrality_score * (1 - visibility_penalty * 0.5)

        scored.append((node, {**m, 'score': score, 'stars': stars}))

    scored.sort(key=lambda x: x[1]['score'], reverse=True)
    return scored[:top_n]


def get_graph_stats(G: nx.MultiDiGraph) -> dict:
    """Get overall graph statistics."""
    simple = nx.DiGraph(G)

    stats = {
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'density': nx.density(simple),
        'avg_in_degree': sum(dict(G.in_degree()).values()) / max(G.number_of_nodes(), 1),
        'avg_out_degree': sum(dict(G.out_degree()).values()) / max(G.number_of_nodes(), 1),
    }

    # connected components (treat as undirected)
    undirected = G.to_undirected()
    stats['num_components'] = nx.number_connected_components(undirected)

    # largest component size
    if stats['num_components'] > 0:
        largest = max(nx.connected_components(undirected), key=len)
        stats['largest_component_size'] = len(largest)
    else:
        stats['largest_component_size'] = 0

    return stats
