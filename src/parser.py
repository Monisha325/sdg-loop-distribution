
import re

def parse_index(expr):

    pattern = r'([A-Za-z]+)\[i([+-]\d+)?\]'
    match = re.match(pattern, expr.strip())

    if not match:
        return None

    array = match.group(1)
    offset = match.group(2)

    if offset is None:
        offset = 0
    else:
        offset = int(offset)

    return (array, offset)


def parse_statement(line):

    label, stmt = line.split(":")
    lhs, rhs = stmt.split("=")

    lhs = lhs.strip()
    rhs = rhs.strip()

    writes = []
    reads = []

    w = parse_index(lhs)

    if w:
        writes.append(w)

    tokens = re.findall(r"[A-Za-z]+\[i[+-]?\d*\]", rhs)

    for t in tokens:
        r = parse_index(t)
        if r:
            reads.append(r)

    return {
        "label": label.strip(),
        "writes": writes,
        "reads": reads
    }


def parse_file(filepath):

    program = []

    with open(filepath) as f:
        for line in f:
            if line.strip():
                program.append(parse_statement(line))

    return program
