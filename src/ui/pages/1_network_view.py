import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.storage import Database
from src.graph import build_graph, filter_graph, get_subgraph_around
from src.ui.components import render_filters, render_graph, render_legend

st.set_page_config(page_title="Network View", layout="wide", initial_sidebar_state="expanded")

# hide sidebar collapse button
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    .st-emotion-cache-1gwvy71 { display: none !important; }
    button[kind="headerNoPadding"] { display: none !important; }
</style>
""", unsafe_allow_html=True)
st.title("🌐 Network View")
st.caption("**Tip:** Click and drag to pan • Scroll to zoom • Click a node to highlight connections • Drag nodes to rearrange")


@st.cache_resource
def get_db():
    return Database()


@st.cache_data
def load_data():
    db = get_db()
    return db.get_all_packages(), db.get_all_dependencies()


packages, deps = load_data()

if not packages:
    st.warning("No data. Run collection script first.")
    st.stop()

# build full graph
G = build_graph(packages, deps)

# focus on specific package (at top of sidebar)
st.sidebar.subheader("Focus", help="Zoom in on a specific package's neighborhood")
pkg_options = ["(none)"] + sorted([p.name for p in packages])

focus_pkg = st.sidebar.selectbox(
    "Center on package",
    pkg_options,
    index=0,
    help="Select a package to view only its local dependency network"
)
focus_depth = st.sidebar.slider(
    "Depth", 1, 3, 2,
    help="How many hops away from the focused package to include"
)

st.sidebar.divider()

# filters
filters = render_filters(packages, show_relation_types=True)

# apply filters
filtered_G = filter_graph(
    G,
    domains=filters['domains'],
    roles=filters['roles'],
    relation_types=filters['relation_types'],
    min_in_degree=filters['min_in_degree']
)

# focus if selected
if focus_pkg != "(none)":
    filtered_G = get_subgraph_around(filtered_G, focus_pkg, depth=focus_depth)

# stats
col1, col2 = st.columns(2)
col1.metric(
    "Visible Nodes", filtered_G.number_of_nodes(),
    help="Number of packages shown after applying filters"
)
col2.metric(
    "Visible Edges", filtered_G.number_of_edges(),
    help="Number of dependency relationships shown after filtering"
)

# render
render_legend()
st.divider()

physics = st.checkbox(
    "Enable physics simulation", value=True,
    help="When enabled, nodes repel each other and settle into a layout. Disable for large graphs."
)
render_graph(filtered_G, height=700, physics=physics)
