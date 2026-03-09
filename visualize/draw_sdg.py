
import matplotlib.pyplot as plt
import networkx as nx
import os

def draw_sdg(G, output_path, name="graph"):

    pos = nx.spring_layout(G)

    colors = []

    for node in G.nodes():

        if G.nodes[node]["parallelizable"]:
            colors.append("green")
        else:
            colors.append("red")

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color=colors,
        node_size=2500
    )

    plt.title("SCC Dependence Graph (SDG)")

    save_path = os.path.join(
        output_path,
        "output",
        "graphs",
        f"{name}_sdg.png"
    )

    plt.savefig(save_path)

    plt.show()

    print("SDG saved at:", save_path)
