
import networkx as nx

def build_sdg(rdg, sccs):

    SDG = nx.DiGraph()

    node_map = {}

    for scc in sccs:

        node_id = scc["id"]

        parallel = (scc["size"] == 1 and scc["loop_carried_edges"] == 0)

        SDG.add_node(
            node_id,
            statements=scc["nodes"],
            size=scc["size"],
            parallelizable=parallel,
            loop_carried_count=scc["loop_carried_edges"]
        )

        for stmt in scc["nodes"]:
            node_map[stmt] = node_id

    for u,v,data in rdg.edges(data=True):

        su = node_map[u]
        sv = node_map[v]

        if su != sv:
            SDG.add_edge(su, sv)

    return SDG
