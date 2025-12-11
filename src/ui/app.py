import streamlit as st
import sys
from pathlib import Path

# add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.storage import Database, Domain
from src.graph import build_graph, get_graph_stats

st.set_page_config(
    page_title="ML Dependency Analyzer",
    page_icon="🔗",
    layout="wide"
)


@st.cache_resource
def get_db():
    return Database()


@st.cache_data
def load_graph_data():
    db = get_db()
    packages = db.get_all_packages()
    deps = db.get_all_dependencies()
    return packages, deps


DOMAIN_TOOLTIPS = {
    'deep_learning': 'Neural network frameworks (PyTorch, TensorFlow, JAX)',
    'traditional_ml': 'Classical ML algorithms (scikit-learn, XGBoost)',
    'data_processing': 'Data manipulation and storage (pandas, numpy)',
    'visualization': 'Plotting and charting libraries (matplotlib, plotly)',
    'nlp': 'Natural language processing tools (transformers, spaCy)',
    'computer_vision': 'Image and video processing (OpenCV, torchvision)',
    'utilities': 'General-purpose helpers (tqdm, requests)',
    'infrastructure': 'Dev tools and deployment (pytest, pip)',
}


def main():
    st.title("ML Dependency Network Analyzer")

    # project context
    with st.expander("About this project", expanded=False):
        st.markdown("""
        **INFO 202 Final Project** — UC Berkeley School of Information

        This tool analyzes dependency relationships in the Python ML ecosystem by:

        1. **Collecting** metadata and dependency files from 100 top ML repositories on GitHub
        2. **Parsing** `pyproject.toml`, `setup.py`, and `requirements.txt` to extract dependencies
        3. **Classifying** packages using a multi-faceted taxonomy (domain, role, health status)
        4. **Building** a directed graph with typed edges representing different dependency relationships
        5. **Computing** network metrics like PageRank and betweenness centrality

        The project demonstrates information science concepts including **ontologies**,
        **faceted classification**, **hierarchical structures**, and **network-based information organization**.

        ---

        **Dependency Types:**
        - `requires_core` — Essential runtime dependency
        - `requires_optional` — Optional feature dependency
        - `requires_dev` — Development/testing only
        - `extends` — Wraps or builds upon another package

        **Classification Facets:**
        - **Domain** — What problem area the package addresses
        - **Role** — Whether it's a framework, library, tool, or extension
        - **Health** — Maintenance status based on commit activity
        """)

    packages, deps = load_graph_data()

    if not packages:
        st.warning("No data found. Run `python scripts/collect_data.py` first.")
        st.stop()

    G = build_graph(packages, deps)
    stats = get_graph_stats(G)

    # summary metrics with tooltips
    st.subheader("Network Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Packages", stats['num_nodes'],
        help="Total number of unique packages discovered across all repositories"
    )
    col2.metric(
        "Dependencies", stats['num_edges'],
        help="Total number of dependency relationships (edges) in the graph"
    )
    col3.metric(
        "Density", f"{stats['density']:.4f}",
        help="Graph density = edges / possible edges. Low density is typical for dependency networks"
    )
    col4.metric(
        "Components", stats['num_components'],
        help="Number of weakly connected components. Ideally 1 (all packages connected)"
    )

    st.divider()

    # domain distribution with tooltips
    st.subheader("Packages by Domain")
    domain_counts = {}
    for pkg in packages:
        d = pkg.domain
        domain_counts[d] = domain_counts.get(d, 0) + 1

    cols = st.columns(len(Domain))
    for i, domain in enumerate(Domain):
        count = domain_counts.get(domain.value, 0)
        tooltip = DOMAIN_TOOLTIPS.get(domain.value, '')
        cols[i].metric(
            domain.value.replace('_', ' ').title(),
            count,
            help=tooltip
        )

    st.divider()

    # quick links with descriptions
    st.subheader("Explore")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/1_network_view.py", label="🌐 Network View", icon="🔗")
        st.caption("Interactive graph visualization with filtering")
    with col2:
        st.page_link("pages/2_package_view.py", label="📦 Package Explorer", icon="📦")
        st.caption("Browse individual packages and their dependencies")
    with col3:
        st.page_link("pages/3_path_explorer.py", label="🛤️ Path Finder", icon="🛤️")
        st.caption("Find dependency paths between packages")


if __name__ == "__main__":
    main()
