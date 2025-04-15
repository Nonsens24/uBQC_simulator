import matplotlib.pyplot as plt
import networkx as nx
import matplotlib.cm as cm
import matplotlib.colors as colors
from fractions import Fraction
import numpy as np

def format_angle(angle, denom=4):
    """Return a string representing angle as a multiple of π/denom."""
    frac = Fraction(angle / np.pi).limit_denominator(denom)
    n = frac.numerator
    d = frac.denominator

    if n == 0:
        return "0"
    elif abs(n) == 1 and d == 1:
        return "π" if n > 0 else "-π"
    elif d == 1:
        return f"{n}π"
    elif abs(n) == 1:
        return f"π/{d}" if n > 0 else f"-π/{d}"
    else:
        return f"{n}π/{d}"

def plot_brickwork_graph_bfk_format(pattern):
    G = nx.Graph()
    coords = {}  # Maps qubit label to (row, col)
    angle_map = {}  # node: angle

    # Build graph with correct (i, j) mapping
    for cmd in pattern.commands:
        if cmd.__dict__['name'] == "N":
            i, j = cmd.__dict__['which_qubits'][0]
            G.add_node((i, j))
            coords[(i, j)] = (j, -i)  # For plotting: X = col (j), Y = row (i), flipped for correct vertical stacking

        elif cmd.__dict__['name'] == "E":
            (i1, j1), (i2, j2) = cmd.__dict__['which_qubits']
            G.add_edge((i1, j1), (i2, j2))

        elif cmd.name == "M": ## Change the graph for testing
            i, j = cmd.which_qubit
            if j < 14:
                cmd.angle = -cmd.angle / 2 #DEBUG
                angle_map[(i, j)] = cmd.angle  # Store angle for node
            else:
                cmd.angle = 0   #Debug change graph to reference state
                angle_map[(i, j)] = 0

    # Assign default angle = 0 to unmeasured nodes
    for node in G.nodes:
        # print("node {}, angle {} ".format(node, angle_map[node]))
        G.nodes[node]['angle'] = angle_map.get(node)

    # Your color assignment style, but aligned with G.nodes
    node_colours = []
    for node in G.nodes:
        if G.nodes[node]['angle'] != 0:
            node_colours.append('tomato')
        else:
            node_colours.append('skyblue')

    # Optional node labels with angle
    labels = {
        node: f"{node}\n{format_angle(G.nodes[node]['angle'])}" for node in G.nodes
    }

    # Plot with grid alignment
    pos = {(i, j): (j, -i) for (i, j) in G.nodes}

    plt.figure(figsize=(12, 6))
    nx.draw(
        G, pos, with_labels=True, labels=labels,
        node_color=node_colours, node_size=600,
        font_size=8, font_weight='bold'
    )
    plt.title("Brickwork Graph in BFK Format")
    plt.axis("off")
    plt.show()