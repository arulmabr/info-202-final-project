from collections import Counter
from ..storage import Package, Dependency, Domain, Role


def infer_from_dependencies(pkg: Package, deps: list[Dependency], all_packages: dict[str, Package]) -> Package:
    """Infer package classification from its dependencies."""
    if pkg.domain != Domain.UTILITIES.value:
        # already classified
        return pkg

    # count domains of dependencies
    domain_counts = Counter()
    for dep in deps:
        if dep.target in all_packages:
            target_pkg = all_packages[dep.target]
            if target_pkg.domain != Domain.UTILITIES.value:
                domain_counts[target_pkg.domain] += 1

    if domain_counts:
        # assign most common domain
        pkg.domain = domain_counts.most_common(1)[0][0]

    return pkg


def infer_from_dependents(pkg: Package, dependents: list[Dependency], all_packages: dict[str, Package]) -> Package:
    """Infer package classification from what depends on it."""
    if pkg.domain != Domain.UTILITIES.value:
        return pkg

    domain_counts = Counter()
    for dep in dependents:
        if dep.source in all_packages:
            source_pkg = all_packages[dep.source]
            if source_pkg.domain != Domain.UTILITIES.value:
                domain_counts[source_pkg.domain] += 1

    if domain_counts:
        pkg.domain = domain_counts.most_common(1)[0][0]

    return pkg


def infer_role_from_centrality(pkg: Package) -> Package:
    """Infer role based on graph centrality metrics."""
    if pkg.role != Role.LIBRARY.value:
        return pkg

    # high in-degree with moderate out-degree = likely framework
    if pkg.in_degree > 10 and pkg.out_degree < pkg.in_degree * 2:
        pkg.role = Role.FRAMEWORK.value
    # very low out-degree but some in-degree = likely utility
    elif pkg.out_degree <= 2 and pkg.in_degree > 0:
        pkg.role = Role.LIBRARY.value

    return pkg


def run_inference(packages: dict[str, Package], dependencies: list[Dependency]) -> dict[str, Package]:
    """Run all inference passes over packages."""
    # build lookup structures
    deps_by_source = {}
    deps_by_target = {}
    for dep in dependencies:
        deps_by_source.setdefault(dep.source, []).append(dep)
        deps_by_target.setdefault(dep.target, []).append(dep)

    # first pass: infer from dependencies
    for name, pkg in packages.items():
        deps = deps_by_source.get(name, [])
        pkg = infer_from_dependencies(pkg, deps, packages)

    # second pass: infer from dependents
    for name, pkg in packages.items():
        dependents = deps_by_target.get(name, [])
        pkg = infer_from_dependents(pkg, dependents, packages)

    # third pass: infer role from centrality
    for pkg in packages.values():
        infer_role_from_centrality(pkg)

    return packages
