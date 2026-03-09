
import networkx as nx

def direction(d):

    if d > 0:
        return "<"
    elif d < 0:
        return ">"
    else:
        return "="


def build_rdg(program):

    G = nx.DiGraph()

    for stmt in program:
        G.add_node(stmt["label"], data=stmt)

    for s1 in program:
        for s2 in program:

            if s1["label"] == s2["label"]:
                continue

            for w_array, w_off in s1["writes"]:

                for r_array, r_off in s2["reads"]:

                    if w_array == r_array:

                        d = r_off - w_off

                        G.add_edge(
                            s1["label"],
                            s2["label"],
                            type="RAW",
                            array=w_array,
                            distance=d,
                            direction=direction(d),
                            loop_carried=(d != 0)
                        )

                for w2_array, w2_off in s2["writes"]:

                    if w_array == w2_array:

                        d = w2_off - w_off

                        G.add_edge(
                            s1["label"],
                            s2["label"],
                            type="WAW",
                            array=w_array,
                            distance=d,
                            direction=direction(d),
                            loop_carried=(d != 0)
                        )

            for r_array, r_off in s1["reads"]:

                for w_array, w_off in s2["writes"]:

                    if r_array == w_array:

                        d = w_off - r_off

                        G.add_edge(
                            s1["label"],
                            s2["label"],
                            type="WAR",
                            array=r_array,
                            distance=d,
                            direction=direction(d),
                            loop_carried=(d != 0)
                        )

    return G
