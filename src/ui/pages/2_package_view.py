import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.storage import Database
from src.graph import build_graph, get_subgraph_around
from src.ui.components import render_filters, apply_filters, render_package_card, render_graph

st.set_page_config(page_title="Package Explorer", layout="wide", initial_sidebar_state="expanded")

# hide sidebar collapse button
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    .st-emotion-cache-1gwvy71 { display: none !important; }
    button[kind="headerNoPadding"] { display: none !important; }
</style>
""", unsafe_allow_html=True)
st.title("📦 Package Explorer")


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

G = build_graph(packages, deps)
pkg_lookup = {p.name: p for p in packages}

# filters
filters = render_filters(packages, show_relation_types=False)
filtered = apply_filters(packages, filters)

# main content - search and sort at top
col_search, col_sort = st.columns([3, 1])
with col_search:
    search = st.text_input("🔍 Search packages", "", placeholder="Type to filter by name...")
with col_sort:
    sort_by = st.selectbox(
        "Sort by",
        ["pagerank", "in_degree", "name", "github_stars"],
        index=0,
        help="PageRank shows most important packages first"
    )

if search:
    filtered = [p for p in filtered if search.lower() in p.name.lower()]

filtered.sort(key=lambda p: getattr(p, sort_by) or 0, reverse=sort_by != "name")

st.caption(f"**{len(filtered)}** packages match filters")

# package list + detail
col_list, col_detail = st.columns([1, 2])

with col_list:
    selected = None
    for pkg in filtered[:50]:
        if st.button(pkg.name, key=f"pkg_{pkg.name}", use_container_width=True):
            selected = pkg.name

    if len(filtered) > 50:
        st.caption(f"... and {len(filtered) - 50} more. Use search to find specific packages.")

# use session state to persist selection
if selected:
    st.session_state['selected_package'] = selected

# default to numpy if nothing selected yet
if 'selected_package' not in st.session_state and 'numpy' in pkg_lookup:
    st.session_state['selected_package'] = 'numpy'

selected = st.session_state.get('selected_package')

with col_detail:
    if selected and selected in pkg_lookup:
        pkg = pkg_lookup[selected]

        # get dependencies and dependents
        pkg_deps = [d for d in deps if d.source == selected]
        pkg_dependents = [d for d in deps if d.target == selected]

        render_package_card(pkg, dependencies=pkg_deps, dependents=pkg_dependents)

        # mini network view
        st.divider()
        st.subheader("Local Network")
        subgraph = get_subgraph_around(G, selected, depth=1)
        render_graph(subgraph, height=400, physics=False)
    else:
        st.info("Select a package from the list to view details.")
