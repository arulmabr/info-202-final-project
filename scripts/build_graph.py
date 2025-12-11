#!/usr/bin/env python3
"""Build dependency graph from collected data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage import Database, Package
from src.parsing import extract_dependencies
from src.ontology import classify_and_assess, refine_dependencies, run_inference
from src.graph import build_graph, update_package_metrics, get_graph_stats, find_hidden_pillars


def main():
    db = Database()

    print("Loading repositories...")
    repos = db.get_all_repositories()
    print(f"Found {len(repos)} repositories")

    if not repos:
        print("No data. Run collect_data.py first.")
        return

    # extract dependencies
    print("\nExtracting dependencies...")
    all_deps = []
    packages = {}

    for repo in repos:
        deps = extract_dependencies(repo)
        deps = refine_dependencies(deps)
        all_deps.extend(deps)

        pkg_name = repo.package_name or repo.full_name.split('/')[-1].lower()

        if pkg_name not in packages:
            pkg = Package(
                name=pkg_name,
                github_repo=repo.full_name,
                description=repo.description,
                github_stars=repo.stars,
                last_commit_date=repo.last_commit,
            )
            pkg = classify_and_assess(pkg)
            packages[pkg_name] = pkg

    # add dependency targets as packages too
    for dep in all_deps:
        if dep.target not in packages:
            pkg = Package(name=dep.target)
            pkg = classify_and_assess(pkg)
            packages[dep.target] = pkg

    print(f"Found {len(packages)} packages and {len(all_deps)} dependencies")

    # build graph and compute metrics
    print("\nBuilding graph...")
    pkg_list = list(packages.values())
    G = build_graph(pkg_list, all_deps)

    print("Computing metrics...")
    pkg_list = update_package_metrics(pkg_list, G)

    # run inference
    print("Running classification inference...")
    packages = {p.name: p for p in pkg_list}
    packages = run_inference(packages, all_deps)

    # save to database
    print("\nSaving to database...")
    for pkg in packages.values():
        db.save_package(pkg)
    db.save_dependencies(all_deps)

    # print stats
    stats = get_graph_stats(G)
    print("\n--- Graph Statistics ---")
    print(f"Nodes: {stats['num_nodes']}")
    print(f"Edges: {stats['num_edges']}")
    print(f"Density: {stats['density']:.4f}")
    print(f"Components: {stats['num_components']}")
    print(f"Largest component: {stats['largest_component_size']} nodes")

    # find hidden pillars
    print("\n--- Hidden Pillars (high centrality, potentially low visibility) ---")
    pillars = find_hidden_pillars(G, top_n=10)
    for name, metrics in pillars:
        print(f"  {name}: pagerank={metrics['pagerank']:.4f}, betweenness={metrics['betweenness']:.4f}")

    print(f"\nDone. Run 'streamlit run src/ui/app.py' to explore.")


if __name__ == "__main__":
    main()
