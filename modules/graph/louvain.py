import networkx as nx
import networkx.algorithms.community as nx_comm
from typing import List, Dict
from config import GLOBAL_SEED, SHELL_CLUSTER_MAX_SIZE, SHELL_CLUSTER_MIN_DENSITY

def detect_shell_clusters(G: nx.Graph) -> List[Dict]:
    """
    Partitions the graph using Louvain community detection and flags
    small, high-density clusters characteristic of shell rings (minimum 3 members).
    """
    if len(G.nodes) == 0 or len(G.edges) == 0:
        return []

    raw_communities = nx_comm.louvain_communities(G, seed=GLOBAL_SEED)
    
    # Sort communities deterministically to eliminate random set iteration order
    communities = sorted(
        [sorted(list(c)) for c in raw_communities],
        key=lambda c: (-len(c), c[0] if c else "")
    )
    
    suspicious_clusters = []

    for idx, community in enumerate(communities):
        if len(community) < 3:
            continue

        subgraph = G.subgraph(community)
        density = nx.density(subgraph)

        if len(community) <= SHELL_CLUSTER_MAX_SIZE and density >= SHELL_CLUSTER_MIN_DENSITY:
            shared_links = []
            for u, v, d in sorted(subgraph.edges(data=True), key=lambda x: (x[0], x[1])):
                shared_links.append([u, v, f"{d.get('shared_field')}:{d.get('shared_value')}"])

            suspicious_clusters.append({
                "cluster_id": f"CLUSTER-{idx+1:02d}",
                "members": list(community),
                "density": round(density, 2),
                "size": len(community),
                "shared_links": shared_links
            })

    return suspicious_clusters