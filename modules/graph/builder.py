import networkx as nx
from collections import defaultdict
from rapidfuzz import fuzz
from typing import List, Dict
from config import FUZZY_MATCH_THRESHOLD


def build_entity_graph(entities: List[Dict]) -> nx.Graph:
    G = nx.Graph()

    for entity in entities:
        G.add_node(
            entity["entity_id"],
            name=entity.get("name", ""),
            directors=entity.get("director_names", []),
            address=entity.get("registered_address", ""),
            phone=entity.get("phone", ""),
            bank_account=entity.get("bank_account", ""),
        )

    phone_map = defaultdict(list)
    bank_map = defaultdict(list)

    for e in entities:
        eid = e["entity_id"]
        if e.get("phone"):
            phone_map[e["phone"]].append(eid)
        if e.get("bank_account"):
            bank_map[e["bank_account"]].append(eid)

    for field_name, attr_map in [("phone", phone_map), ("bank_account", bank_map)]:
        for val in sorted(attr_map.keys()):
            ids = attr_map[val]
            if len(ids) > 1:
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        G.add_edge(
                            ids[i], ids[j], shared_field=field_name, shared_value=val
                        )

    n = len(entities)
    for i in range(n):
        e1 = entities[i]
        id1 = e1["entity_id"]

        for j in range(i + 1, n):
            e2 = entities[j]
            id2 = e2["entity_id"]

            addr1, addr2 = e1.get("registered_address", ""), e2.get(
                "registered_address", ""
            )
            if addr1 and addr2:
                if fuzz.token_sort_ratio(addr1, addr2) >= FUZZY_MATCH_THRESHOLD:
                    G.add_edge(
                        id1, id2, shared_field="registered_address", shared_value=addr1
                    )

            for d1 in e1.get("director_names", []):
                for d2 in e2.get("director_names", []):
                    if fuzz.ratio(d1, d2) >= FUZZY_MATCH_THRESHOLD:
                        G.add_edge(id1, id2, shared_field="director", shared_value=d1)

    return G
