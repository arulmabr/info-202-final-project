import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.storage import Database
from src.graph import build_graph, find_all_paths, get_path_details
from src.ui.components import render_graph

st.set_page_config(page_title="Path Explorer", layout="wide")
st.title("🛤️ Path Explorer")

with st.expander("How path finding works", expanded=False):
    st.markdown("""
**Dependency paths** show how packages are connected through their dependencies.

**Direction matters:** Paths follow dependency direction (A → B means A *depends on* B).
- ✅ `transformers → numpy` works (transformers depends on numpy)
- ❌ `numpy → transformers` won't find a path (numpy doesn't depend on transformers)

**Why no path found?**
- The source doesn't depend on the target (try swapping them)
- The path is longer than max length (increase the slider)
- Packages are in disconnected parts of the graph

**Why multiple paths?**
Some packages can be reached through different dependency chains.
For example, `mlflow → numpy` could go through `pandas`, `scipy`, or directly.
""")


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
pkg_names = sorted([p.name for p in packages])

# interesting defaults - mlflow -> certifi shows a 3-hop path through requests
def get_index(name, fallback=0):
    try:
        return pkg_names.index(name)
    except ValueError:
        return fallback

# inputs
col1, col2 = st.columns(2)
with col1:
    source = st.selectbox(
        "From package", pkg_names,
        index=get_index("mlflow", get_index("transformers", 0)),
        help="Starting package — finds dependencies of this package"
    )
with col2:
    target = st.selectbox(
        "To package", pkg_names,
        index=get_index("certifi", get_index("numpy", 1)),
        help="Target package — searches for this as a direct or transitive dependency"
    )

max_paths = st.slider(
    "Max paths to find", 1, 10, 3,
    help="Limit how many alternative paths to display"
)
max_length = st.slider(
    "Max path length", 2, 8, 5,
    help="Maximum hops between packages (longer = slower but finds more paths)"
)

if st.button("Find Paths", type="primary"):
    if source == target:
        st.warning("Select different packages")
    else:
        paths = find_all_paths(G, source, target, max_length=max_length)

        if not paths:
            st.error(f"No path found from **{source}** to **{target}**")
            st.caption("Try swapping source ↔ target, or increase max path length. See \"How path finding works\" above.")
        else:
            st.success(f"Found {len(paths)} path(s)")

            for i, path in enumerate(paths[:max_paths]):
                with st.expander(f"Path {i+1}: {' → '.join(path)} (length {len(path)-1})"):
                    details = get_path_details(G, path)

                    # show step by step
                    for j, step in enumerate(details):
                        cols = st.columns([1, 2, 1])
                        cols[0].markdown(f"**{step['package']}**")
                        cols[1].markdown(f"`{step['domain']}` / `{step['role']}`")

                        if 'edge_type' in step:
                            cols[2].markdown(f"↓ _{step['edge_type']}_")

                    # mini graph of path
                    path_nodes = set(path)
                    subgraph = G.subgraph(path_nodes).copy()
                    render_graph(subgraph, height=300, physics=False)

            # summary
            if len(paths) > max_paths:
                st.info(f"Showing {max_paths} of {len(paths)} paths")

# common dependencies finder
st.divider()
st.subheader("Find Common Dependencies")

with st.expander("How this works", expanded=False):
    st.markdown("""
Finds **direct dependencies** that all selected packages share.

**Why no common dependencies?**
- Packages may use different libraries for similar tasks
- Some packages have few dependencies (e.g., `torch` has minimal direct deps)
- Only *direct* dependencies are checked, not transitive ones

**Good examples to try:**
- HuggingFace ecosystem: `transformers`, `diffusers`, `accelerate` → share `huggingface-hub`, `numpy`
- MLOps tools: `mlflow`, `wandb`, `optuna` → share `numpy`, `packaging`
""")

# default to HuggingFace packages which share common deps
default_common = [p for p in ["transformers", "diffusers", "accelerate"] if p in pkg_names]
selected_pkgs = st.multiselect(
    "Select packages", pkg_names,
    default=default_common,
    help="Select 2+ packages to find dependencies they all share"
)

if len(selected_pkgs) >= 2:
    common = set(G.successors(selected_pkgs[0]))
    for pkg in selected_pkgs[1:]:
        if pkg in G:
            common &= set(G.successors(pkg))

    if common:
        st.markdown(f"**{len(common)} common dependencies:**")
        st.write(", ".join(sorted(common)))
    else:
        st.info("No common direct dependencies found. These packages may use different libraries or have minimal dependencies.")
elif len(selected_pkgs) == 1:
    st.caption("Select at least 2 packages to compare")
