
import networkx as nx

def compute_scc(G):

    sccs = list(nx.strongly_connected_components(G))

    results = []

    for i, comp in enumerate(sccs):

        loop_carried = 0
        has_cycle = len(comp) > 1

        for u in comp:
            for v in comp:

                if G.has_edge(u, v):

                    if G[u][v]["loop_carried"]:
                        loop_carried += 1

        results.append({
            "id": f"SCC{i+1}",
            "nodes": list(comp),
            "size": len(comp),
            "has_cycle": has_cycle,
            "loop_carried_edges": loop_carried
        })

    return results
