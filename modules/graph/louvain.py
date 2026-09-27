import networkx as nx
import networkx.algorithms.community as nx_comm
from typing import List, Dict
from config import GLOBAL_SEED, SHELL_CLUSTER_MAX_SIZE, SHELL_CLUSTER_MIN_DENSITY

def detect_shell_clusters(G: nx.Graph) -> List[Dict]:
    """
    Partitions the graph using Louvain community detection and flags
    small, high-density clusters characteristic of shell rings.
    """
    if len(G.nodes) == 0 or len(G.edges) == 0:
        return []

    # Deterministic community detection using seed
    communities = nx_comm.louvain_communities(G, seed=GLOBAL_SEED)
    suspicious_clusters = []

    for idx, community in enumerate(communities):
        if len(community) < 2:
            continue

        subgraph = G.subgraph(community)
        density = nx.density(subgraph)

        # Flag small, dense groups (3 to 8 entities with density > 0.5)
        if len(community) <= SHELL_CLUSTER_MAX_SIZE and density >= SHELL_CLUSTER_MIN_DENSITY:
            shared_links = []
            for u, v, d in subgraph.edges(data=True):
                shared_links.append([u, v, f"{d.get('shared_field')}:{d.get('shared_value')}"])

            suspicious_clusters.append({
                "cluster_id": f"CLUSTER-{idx+1:02d}",
                "members": list(community),
                "density": round(density, 2),
                "size": len(community),
                "shared_links": shared_links
            })

    return suspicious_clusters