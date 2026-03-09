
import matplotlib.pyplot as plt
import networkx as nx
import os

def draw_rdg(G, output_path, name="graph"):

    pos = nx.spring_layout(G)

    labels = {}
    edge_colors = []

    for u, v, data in G.edges(data=True):

        labels[(u, v)] = f"{data['type']} d={data['distance']}"

        if data["type"] == "RAW":
            edge_colors.append("red")
        elif data["type"] == "WAR":
            edge_colors.append("blue")
        else:
            edge_colors.append("green")

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color="lightblue",
        edge_color=edge_colors,
        node_size=2000
    )

    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)

    plt.title("Reduced Dependence Graph (RDG)")

    save_path = os.path.join(
        output_path,
        "output",
        "graphs",
        f"{name}_rdg.png"
    )

    plt.savefig(save_path)
    plt.show()

    print("RDG saved at:", save_path)
