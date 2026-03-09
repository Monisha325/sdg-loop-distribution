
from graphviz import Digraph
import os


def draw_sdg_paper_style(SDG, output_path):

    dot = Digraph(comment="SCC Dependence Graph")

    dot.attr(rankdir="LR")   # left to right layout


    for node in SDG.nodes():

        data = SDG.nodes[node]

        statements = "\n".join(data["statements"])

        label = f"{node}\n---\n{statements}"

        if data["parallelizable"]:
            color = "green"
        else:
            color = "red"

        dot.node(
            node,
            label,
            shape="rectangle",
            style="filled",
            fillcolor=color
        )


    for u, v in SDG.edges():
        dot.edge(u, v)


    save_path = os.path.join(output_path, "output", "graphs", "sdg_paper")

    dot.render(save_path, format="png", cleanup=True)

    print("Paper-style SDG saved at:", save_path + ".png")
