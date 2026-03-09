
import json

def export_sdg_json(G, output_file):

    data = {
        "nodes": [],
        "edges": []
    }

    for node in G.nodes():

        node_data = {
            "id": node,
            "statements": G.nodes[node]["statements"],
            "size": G.nodes[node]["size"],
            "parallelizable": G.nodes[node]["parallelizable"],
            "loop_carried_count": G.nodes[node]["loop_carried_count"]
        }

        data["nodes"].append(node_data)

    for u, v in G.edges():

        edge_data = {
            "from": u,
            "to": v
        }

        data["edges"].append(edge_data)

    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)

    print("SDG JSON exported to:", output_file)
