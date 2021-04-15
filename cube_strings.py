"""cube_strings: strings that represent hypercubes, together with
operations on them.

Cube strings are in the directory ./qstrings.

Each string of the form Q{dimension}STRING has codes for the
following elements of a hypercube:

- Vertices (like `[0010]`). These are bit strings that represent
  the locations of vertices in a VertexSet.  For example,
  `[0010]` would only correspond to vertex `[0010]` before any
  automorphism had been applied to the cube.

- Edge strings (like `(1-----3)`). These represent part of an
  edge between vertices at the given locations.

Why am I using binary in the vertices, and decimal for the edges?
Well, an n-dimensional hypercube has vertices given by all
possible n-length bit-strings. It would be nice to use binary for
*all* the codes---but then the edges would be hard to recognize
by sight---and they'd get significantly uglier with higher
dimensions.

"""

import re
from colorama import Style
import bits

def copy_contents_to_string(filename):
    file_object = open(filename, "r")
    string = file_object.read()
    file_object.close()
    return string

Q0STRING = copy_contents_to_string("./qstrings/q0.qstring")
Q1STRING = copy_contents_to_string("./qstrings/q1.qstring")
Q2STRING = copy_contents_to_string("./qstrings/q2.qstring")
Q3STRING = copy_contents_to_string("./qstrings/q3.qstring")
Q4STRING = copy_contents_to_string("./qstrings/q4.qstring")
Q5STRING = copy_contents_to_string("./qstrings/q5.qstring")

def color_edges(q_string, edge_set):
    """Color the edges in q_string according to edge_set."""
    result = q_string
    all_edge_strings = re.findall(r"\(([0-9]+)"
                                + r"([\\:'`,;.|/-]+)"
                                + r"([0-9]+)\)",
                                  result)
    for low_index, edge_string, high_index in all_edge_strings:
        edge_color = edge_set.lookup_color_by_locations(int(low_index),
                                                        int(high_index))
        if edge_color is None:
            raise ValueError(f"The edge {(low_index, high_index)} "
                             +"doesn't exist.")
        result = result.replace(f"({low_index}{edge_string}{high_index})",
                                f"{edge_color+Style.BRIGHT}{edge_string}{Style.RESET_ALL}")
    return result

def format_vertices(q_string, vertex_set):
    """Replace each vertex location code in `q_string` with the
    colored vertex string for the vertex at that location.

    """
    new_string = q_string
    all_vertex_codes = re.findall(r"\[([01]+)\]", new_string)
    for location_string in all_vertex_codes:
        location = bits.bit_string_to_int(location_string)
        vertex = vertex_set.lookup_vertex_by_location(location)
        if vertex is None:
            raise ValueError(f"The vertex at location {location} "
                             + "does not exist.")
        new_string = new_string.replace(f"[{location_string}]",
                                      vertex.to_string())
    return new_string

def formatq_string(q_string, edge_set, vertex_set):
    """Format `q_string` correctly according to edge_set and vertex_set."""
    return format_vertices(color_edges(q_string, edge_set),
                          vertex_set)

def draw(cube):
    """Print the hypercube `cube`."""
    dimension = cube.dimension
    strings = {
        0 : Q0STRING,
        1 : Q1STRING,
        2 : Q2STRING,
        3 : Q3STRING,
        4 : Q4STRING,
        5 : Q5STRING
    }

    q_string = strings.get(dimension, None)
    if q_string is None:
        print(f"Sorry, I don't know how to draw dimension {dimension}.")
    else:
        print(formatq_string(q_string, cube.edge_set, cube.vertex_set))
