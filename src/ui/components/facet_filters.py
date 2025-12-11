import streamlit as st
from ...storage import Domain, Role, HealthStatus, RelationType


ROLE_TOOLTIPS = {
    'framework': 'Primary ML framework that structures an application',
    'library': 'Reusable functionality for specific tasks',
    'tool': 'CLI or developer utility',
    'extension': 'Extends or wraps another package',
}

HEALTH_TOOLTIPS = {
    'active': 'Recent commits within 90 days',
    'stable': 'Mature, commits within past year',
    'declining': 'No commits for over a year',
    'unknown': 'Cannot determine status',
}

RELATION_TOOLTIPS = {
    'requires_core': 'Essential runtime dependency',
    'requires_optional': 'Optional feature dependency',
    'requires_dev': 'Development/testing only',
    'extends': 'Wraps or builds upon another package',
}


def render_filters(packages: list, show_relation_types: bool = True) -> dict:
    """Render faceted navigation sidebar and return filter selections."""

    st.sidebar.header("Filters")

    # count facets
    domain_counts = {}
    role_counts = {}
    health_counts = {}

    for pkg in packages:
        domain_counts[pkg.domain] = domain_counts.get(pkg.domain, 0) + 1
        role_counts[pkg.role] = role_counts.get(pkg.role, 0) + 1
        health_counts[pkg.health_status] = health_counts.get(pkg.health_status, 0) + 1

    # domain filter
    st.sidebar.subheader("Domain", help="Problem area the package addresses")
    selected_domains = []
    for domain in Domain:
        count = domain_counts.get(domain.value, 0)
        label = f"{domain.value.replace('_', ' ').title()} ({count})"
        if st.sidebar.checkbox(label, value=True, key=f"domain_{domain.value}"):
            selected_domains.append(domain.value)

    # role filter
    st.sidebar.subheader("Role", help="Type of package: framework, library, tool, or extension")
    selected_roles = []
    for role in Role:
        count = role_counts.get(role.value, 0)
        tooltip = ROLE_TOOLTIPS.get(role.value, '')
        label = f"{role.value.title()} ({count})"
        if st.sidebar.checkbox(label, value=True, key=f"role_{role.value}", help=tooltip):
            selected_roles.append(role.value)

    # health filter
    st.sidebar.subheader("Health Status", help="Maintenance status based on recent commit activity")
    selected_health = []
    for health in HealthStatus:
        count = health_counts.get(health.value, 0)
        tooltip = HEALTH_TOOLTIPS.get(health.value, '')
        label = f"{health.value.title()} ({count})"
        if st.sidebar.checkbox(label, value=True, key=f"health_{health.value}", help=tooltip):
            selected_health.append(health.value)

    # relation type filter (for graph view)
    selected_relations = None
    if show_relation_types:
        st.sidebar.subheader("Relation Types", help="Types of dependency relationships to show")
        selected_relations = []
        for rel in RelationType:
            # default: hide dev dependencies
            default = rel != RelationType.REQUIRES_DEV
            label = rel.value.replace('_', ' ').title()
            tooltip = RELATION_TOOLTIPS.get(rel.value, '')
            if st.sidebar.checkbox(label, value=default, key=f"rel_{rel.value}", help=tooltip):
                selected_relations.append(rel.value)

    # centrality filter
    st.sidebar.subheader("Centrality", help="Filter by package importance")
    min_in_degree = st.sidebar.slider(
        "Min In-Degree", 0, 50, 0,
        help="Minimum number of packages that must depend on a package"
    )

    return {
        'domains': selected_domains,
        'roles': selected_roles,
        'health': selected_health,
        'relation_types': selected_relations,
        'min_in_degree': min_in_degree,
    }


def apply_filters(packages: list, filters: dict) -> list:
    """Apply filter selections to package list."""
    filtered = []
    for pkg in packages:
        if filters['domains'] and pkg.domain not in filters['domains']:
            continue
        if filters['roles'] and pkg.role not in filters['roles']:
            continue
        if filters['health'] and pkg.health_status not in filters['health']:
            continue
        if pkg.in_degree < filters['min_in_degree']:
            continue
        filtered.append(pkg)
    return filtered
