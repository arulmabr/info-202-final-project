import streamlit as st
from ...storage import Package, Dependency, RelationType


def render_package_card(pkg: Package, dependencies: list[Dependency] = None, dependents: list[Dependency] = None):
    """Render a detailed package information card."""

    st.subheader(pkg.name)

    # badges with tooltips
    col1, col2, col3 = st.columns(3)
    col1.markdown(
        f"**Domain:** `{pkg.domain}` "
        "<span title='Problem area this package addresses'>ℹ️</span>",
        unsafe_allow_html=True
    )
    col2.markdown(
        f"**Role:** `{pkg.role}` "
        "<span title='Framework, library, tool, or extension'>ℹ️</span>",
        unsafe_allow_html=True
    )
    col3.markdown(
        f"**Health:** `{pkg.health_status}` "
        "<span title='Maintenance status based on commit activity'>ℹ️</span>",
        unsafe_allow_html=True
    )

    # description
    if pkg.description:
        st.markdown(pkg.description)

    # metrics with tooltips
    st.markdown("**Metrics**")
    cols = st.columns(4)
    cols[0].metric(
        "In-Degree", pkg.in_degree,
        help="Number of packages that depend on this package"
    )
    cols[1].metric(
        "Out-Degree", pkg.out_degree,
        help="Number of packages this package depends on"
    )
    cols[2].metric(
        "PageRank", f"{pkg.pagerank:.4f}",
        help="Importance score based on dependency links (like Google's PageRank)"
    )
    cols[3].metric(
        "Betweenness", f"{pkg.betweenness:.4f}",
        help="How often this package lies on shortest paths between others (bridge score)"
    )

    # github info
    if pkg.github_stars:
        st.markdown(f"⭐ **{pkg.github_stars:,}** stars")
    if pkg.github_repo:
        st.markdown(f"📂 [{pkg.github_repo}](https://github.com/{pkg.github_repo})")

    # dependencies
    if dependencies:
        st.markdown("---")
        st.markdown("**Dependencies**")
        render_dependency_list(dependencies, group_by_type=True)

    # dependents
    if dependents:
        st.markdown("---")
        st.markdown("**Dependents** (packages that depend on this)")
        render_dependency_list(dependents, group_by_type=True, show_source=True)


def render_dependency_list(deps: list[Dependency], group_by_type: bool = False, show_source: bool = False):
    """Render a list of dependencies."""
    if not deps:
        st.caption("None")
        return

    if group_by_type:
        grouped = {}
        for d in deps:
            grouped.setdefault(d.relation_type, []).append(d)

        for rel_type in RelationType:
            type_deps = grouped.get(rel_type, [])
            if type_deps:
                label = rel_type.value.replace('_', ' ').title()
                with st.expander(f"{label} ({len(type_deps)})"):
                    for d in type_deps:
                        name = d.source if show_source else d.target
                        version = f" `{d.version_constraint}`" if d.version_constraint else ""
                        st.markdown(f"- {name}{version}")
    else:
        for d in deps:
            name = d.source if show_source else d.target
            version = f" `{d.version_constraint}`" if d.version_constraint else ""
            st.markdown(f"- {name}{version}")


def render_package_mini(pkg: Package):
    """Render a minimal package summary."""
    st.markdown(f"**{pkg.name}** - {pkg.domain} / {pkg.role}")
    if pkg.description:
        st.caption(pkg.description[:100] + "..." if len(pkg.description) > 100 else pkg.description)
