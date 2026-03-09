
import networkx as nx

def topo_walk(SDG):

    order = list(nx.topological_sort(SDG))

    walk = []

    for node in order:

        data = SDG.nodes[node]

        action = "SPLIT" if data["parallelizable"] else "KEEP"

        walk.append((node, action, data["statements"]))

    return walk
