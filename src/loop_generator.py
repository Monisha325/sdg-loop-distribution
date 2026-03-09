
import os

def generate_loops(walk, project_path, name="output"):

    loops = []

    for node, action, stmts in walk:

        if action == "SPLIT":
            code = "#pragma omp parallel for\n"
            code += "for(int i=0;i<N;i++){\n"
        else:
            code = "for(int i=0;i<N;i++){\n"

        for s in stmts:
            code += "   " + s + ";\n"

        code += "}\n\n"

        loops.append(code)

    final_code = "".join(loops)

    output_file = os.path.join(
        project_path,
        "output",
        "loops",
        f"{name}_distributed.c"
    )

    with open(output_file, "w") as f:
        f.write(final_code)

    print("Distributed loops saved to:", output_file)

    return final_code
