import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
import networkx as nx
import tempfile
import os

# color scheme for domains
DOMAIN_COLORS = {
    'deep_learning': '#e74c3c',
    'traditional_ml': '#3498db',
    'data_processing': '#2ecc71',
    'visualization': '#9b59b6',
    'nlp': '#f39c12',
    'computer_vision': '#1abc9c',
    'utilities': '#95a5a6',
    'infrastructure': '#34495e',
}

RELATION_COLORS = {
    'requires_core': '#2c3e50',
    'requires_optional': '#7f8c8d',
    'requires_dev': '#bdc3c7',
    'extends': '#e67e22',
}


def render_graph(G: nx.MultiDiGraph, height: int = 600, physics: bool = True) -> None:
    """Render a NetworkX graph using PyVis."""
    if len(G) == 0:
        st.info("No nodes to display with current filters.")
        return

    net = Network(height=f"{height}px", width="100%", directed=True, bgcolor="#ffffff")

    # configure physics
    if physics:
        net.set_options('''
        {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "springLength": 100
                },
                "solver": "forceAtlas2Based",
                "stabilization": {"iterations": 100}
            }
        }
        ''')
    else:
        net.toggle_physics(False)

    # add nodes
    max_pagerank = max((G.nodes[n].get('pagerank', 0) for n in G.nodes()), default=1) or 1

    for node in G.nodes():
        data = G.nodes[node]
        domain = data.get('domain', 'utilities')
        pagerank = data.get('pagerank', 0)

        size = 10 + (pagerank / max_pagerank) * 40
        color = DOMAIN_COLORS.get(domain, '#95a5a6')

        title = f"{node}\n"
        title += f"Domain: {domain}\n"
        title += f"Role: {data.get('role', 'unknown')}\n"
        title += f"In-degree: {G.in_degree(node)}\n"
        title += f"PageRank: {pagerank:.4f}"

        net.add_node(node, label=node, size=size, color=color, title=title)

    # add edges
    for u, v, data in G.edges(data=True):
        rel_type = data.get('relation_type', 'requires_core')
        color = RELATION_COLORS.get(rel_type, '#2c3e50')
        net.add_edge(u, v, color=color, title=rel_type)

    # render
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w') as f:
        net.save_graph(f.name)
        f.seek(0)
        html = open(f.name).read()
        components.html(html, height=height + 50)
        os.unlink(f.name)


def render_legend():
    """Render a legend for the graph colors."""
    st.markdown("**Domain Colors**")
    cols = st.columns(4)
    for i, (domain, color) in enumerate(DOMAIN_COLORS.items()):
        label = domain.replace('_', ' ').title()
        cols[i % 4].markdown(f'<span style="color:{color}">●</span> {label}', unsafe_allow_html=True)

    st.markdown("**Edge Types**")
    cols = st.columns(4)
    for i, (rel, color) in enumerate(RELATION_COLORS.items()):
        label = rel.replace('_', ' ').title()
        cols[i % 4].markdown(f'<span style="color:{color}">—</span> {label}', unsafe_allow_html=True)
