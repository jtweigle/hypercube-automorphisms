"""cubes: an implementation of hypercubes with operations for
coloring vertices and edges, and applying automorphisms.

"""

from colorama import Style
import bits
import cube_strings

class Vertex:
    """A vertex in a hypercube."""
    def __init__(self, vertex_id, dimension=0):
        self.color_string = None
        self.vertex_id    = vertex_id
        self.dimension    = dimension

    def to_string(self):
        """Render the vertex as a (possibly colored) string."""
        bit_string = bits.int_to_bit_string(self.vertex_id,
                                            self.dimension)
        if self.color_string is None:
            return bit_string
        return self.color_string + bit_string + Style.RESET_ALL

    def color(self, color_string):
        """Color the vertex according to a colorama string."""
        self.color_string = color_string

class VertexSet:
    """The vertex set for a hypercube.

    This defines a mapping from locations to `Vertex`
    objects. Since each location is already an integer in the
    range of the number of vertices, we can use just a list.

    """
    def __init__(self, dimension=0):
        self.dimension = dimension
        # 2 to the power of dimension:
        number_of_vertices = bits.how_many_bit_strings(self.dimension)
        self.vertices = [Vertex(i, self.dimension) for i
                         in range(number_of_vertices)]

    def lookup_vertex_by_location(self, location):
        """Return the `Vertex` object at the given location,
        or `None` if none exists. """
        try:
            vertex = self.vertices[location]
        except IndexError:
            return None
        return vertex

    def lookup_id_by_location(self, location):
        """Return the `vertex_id` of the vertex at `location`, or
        `None` if none exists.

        """
        vertex = self.lookup_vertex_by_location(location)
        if vertex is None:
            return None
        return vertex.vertex_id

    def lookup_location_by_id(self, vertex_id):
        """Return the location of the vertex with `vertex_id`, or `None` if
        none exists.

        """
        try:
            location = next(location for location, vertex
                            in enumerate(self.vertices)
                            if vertex_id == vertex.vertex_id)
        except StopIteration:
            return None
        return location

    def lookup_vertex_by_id(self, vertex_id):
        """Return the `Vertex` object with `vertex_id`, or `None` if none
        exists.

        """
        location = self.lookup_location_by_id(vertex_id)
        if location is None:
            return None
        return self.vertices[location]

    def color_by_id(self, vertex_id, color_string):
        """Color the given vertex with the given color_string."""
        vertex = self.lookup_vertex_by_id(vertex_id)
        if vertex is None:
            raise ValueError(f"Vertex {vertex_id} does not exist.")
        vertex.color(color_string)

    def uncolor_by_id(self, vertex_id):
        """Remove the color of the given vertex."""
        self.color_by_id(vertex_id, "")

    def color_by_location(self, location, color_string):
        """Color the vertex at `location` with `color_string`."""
        vertex_id = self.lookup_id_by_location(location)
        self.color_by_id(vertex_id, color_string)

    def color_vertices_by_id_list(self, vertex_ids, color_string):
        """Color all given vertex_ids with the color_string."""
        for vertex_id in vertex_ids:
            self.color_by_id(vertex_id, color_string)

    def uncolor_vertices_by_id_list(self, vertex_ids):
        """Remove the color of the given vertex_ids."""
        self.color_vertices_by_id_list(vertex_ids, "")

    def apply_to_all_vertices(self, function):
        """Apply the function to all vertices."""
        list_of_vertices = [vertex for location,vertex in self.vertices.items()]
        for vertex in list_of_vertices:
            function(vertex)

    def map_to_locations(self, function):
        """Rearrange the vertices by sending each from
        location to function(location).

        This `function` will mess up your vertex list unless it's a
        bijection on indices of the vertex list.

        """
        # We must make a copy, because we're swapping.
        vertices = self.vertices.copy()
        for location, vertex in enumerate(vertices):
            self.vertices[function(location)]=vertex

    def map_to_locations_not_colors(self, function):
        """Rearrange the vertices by sending each from
        location to function(location), but leave colors where
        they are.

        As with `map_to_locations`, this `function` will mess up
        your vertex list unless it's a bijection on indices of
        the vertex list.

        """
        vertices = self.vertices.copy()
        color_mapping = dict()
        for location, vertex in enumerate(vertices):
            new_location = function(location)
            color_mapping[location] = vertex.color_string
            self.vertices[new_location] = vertex
        for location, color_string in color_mapping.items():
            self.color_by_location(location, color_string)

    def rotate(self, rotation_list, preserve_colors=False):
        """Permute the bits of every vertex by `rotation_list`, which is a
        list of indices.

        If `preserve_colors` is True, then colors don't follow
        vertices around: they stay where they are.

        """
        def permute_bits(location):
            return bits.permute_bits_by_index_list(location,
                                                   rotation_list,
                                                   self.dimension)
        if preserve_colors:
            self.map_to_locations_not_colors(permute_bits)
        else:
            self.map_to_locations(permute_bits)

    def reflect(self, bit_mask, preserve_colors=False):
        """Flip the bits of every vertex by `bit_mask`.

        If `preserve_colors` is True, then colors don't follow
        vertices around: they stay where they are.

        """
        bit_mask = bits.truncate_within_dimension(bit_mask, self.dimension)
        def flip_function(location):
            return location ^ bit_mask

        if preserve_colors:
            self.map_to_locations_not_colors(flip_function)
        else:
            self.map_to_locations(flip_function)

    def reset_positions(self):
        """Reset the positions of all the vertices."""
        vertices = self.vertices.copy()
        for vertex in vertices:
            self.vertices[vertex.vertex_id] = vertex

class EdgeSet:
    """The edge set for a hypercube.

    This really just defines a mapping from vertex_id pairs (u,v) to
    a color string.

    """
    def __init__(self, vertex_set):
        self.vertex_set = vertex_set
        self.dimension = self.vertex_set.dimension
        # 2 to the power of dimension:
        number_of_vertices = bits.how_many_bit_strings(self.dimension)
        self.edges = dict()

        for low_index in range(number_of_vertices):
            for high_index in range(low_index, number_of_vertices):
                if bits.weight(low_index ^ high_index) == 1:
                    self.edges[(low_index, high_index)] = ""

    def lookup_edge_id_by_locations(self, u_location, v_location):
        """Returns the vertex ID pair specifying
        an edge between vertices at locations u_location and
        v_location, or None if there's no edge between them.

        """
        u_id = self.vertex_set.lookup_id_by_location(u_location)
        v_id = self.vertex_set.lookup_id_by_location(v_location)
        if (u_id, v_id) in self.edges:
            return (u_id, v_id)
        if (v_id, u_id) in self.edges:
            return (v_id, u_id)
        return None

    def color_by_locations(self, u_location, v_location, color_string):
        """Color the edge between locations u_location and v_location with
        the given color_string.

        """
        edge = self.lookup_edge_id_by_locations(u_location, v_location)
        if edge is None:
            raise ValueError(f"({u_location}, {v_location}) is not an edge.")
        id_1 = edge[0]
        id_2 = edge[1]
        self.color_by_ids(id_1, id_2, color_string)

    def uncolor_by_locations(self, u_location, v_location):
        """Remove the color of the edge between locations u_location and
        v_location.

        """
        self.color_by_locations(u_location, v_location, "")

    def color_by_ids(self, u_id, v_id, color_string):
        """Color the edge between vertices u_id and v_id with the
        given color_string.

        """
        if (u_id, v_id) in self.edges:
            self.edges[(u_id,v_id)] = color_string
        elif (v_id, u_id) in self.edges:
            self.edges[(v_id, u_id)] = color_string
        else:
            raise ValueError(f"Vertices {u_id} and {v_id} "
                             +"do not have an edge between them.")

    def uncolor_by_ids(self, u_id, v_id):
        """Remove the color of the edge between vertices u_id and v_id by
        the given color_string.

        """
        self.color_by_ids(u_id, v_id, "")

    def get_induced_edges_from_id_list(self, vertex_id_list):
        """Return the list of edge IDs in the subgraph induced by
        vertex_id_list, where an edge must have both vertices in
        vertex_id_list.

        """
        edge_list = []
        length = len(vertex_id_list)
        for i in range(length):
            for j in range(i, length):
                edge = (vertex_id_list[i], vertex_id_list[j])
                if edge in self.edges:
                    edge_list.append(edge)
        return edge_list

    def color_edges_by_id_list(self, vertex_id_list, color_string):
        """Color the edges in the subgraph induced by `vertex_id_list`
        (a list of `vertex_id`s) with `color_string`.

        """
        induced_edges = self.get_induced_edges_from_id_list(vertex_id_list)
        for low_index, high_index in induced_edges:
            self.color_by_ids(low_index, high_index, color_string)

    def uncolor_edges_by_id_list(self, vertex_id_list):
        """Remove the color of the vertices in the subgraph induced by
        vertex_id_list with color_string.

        """
        self.color_edges_by_id_list(vertex_id_list, "")

    def lookup_color_by_vertex_ids(self, u_id, v_id):
        """Return the `color_string` that matches the edge between
        vertices with `vertex_id`s given by `u_id` and `v_id`, or
        `None` if no such edge exists.

        """
        if (u_id, v_id) in self.edges:
            return self.edges[(u_id, v_id)]
        if (v_id, u_id) in self.edges:
            return self.edges[(v_id, u_id)]
        return None

    def lookup_color_by_locations(self, u_location, v_location):
        """Return the `color_string` that matches the edge between
        vertices at `u_location` and `v_location`, or `None` if
        no such edge exists.

        """
        edge = self.lookup_edge_id_by_locations(u_location, v_location)
        if edge is None:
            return None
        u_id = edge[0]
        v_id = edge[1]
        return self.lookup_color_by_vertex_ids(u_id, v_id)

class Cube:
    """A hypercube."""
    def __init__(self, dimension):
        self.dimension = dimension
        self.vertex_set = VertexSet(self.dimension)
        self.edge_set = EdgeSet(self.vertex_set)

    def rotate(self, rotation_list, preserve_colors=False):
        """Rotate the cube by permuting the bits of every vertex by the
        given rotation_list.

        If `preserve_colors` is True, the rotation won't change
        the position of the colors.

        """
        self.vertex_set.rotate(rotation_list, preserve_colors)

    def reflect(self, bit_mask, preserve_colors=False):
        """Reflect the cube by flipping the bits of every vertex using
        the given bit_mask.

        If `preserve_colors` is True, the reflection won't change
        the position of the colors.

        """
        self.vertex_set.reflect(bit_mask, preserve_colors)

    def reset_positions(self):
        """Reset the positions of all vertices in the cube."""
        self.vertex_set.reset_positions()

    def color_vertices_by_id_list(self, vertex_id_list, color_string):
        """Color the vertices in the given vertex_id_list
        by color_string."""
        self.vertex_set.color_vertices_by_id_list(vertex_id_list, color_string)

    def uncolor_vertices_by_id_list(self, vertex_id_list):
        """Remove the color in the given vertex_id_list."""
        self.vertex_set.uncolor_vertices_by_id_list(vertex_id_list)

    def color_edges_by_id_list(self, vertex_id_list, color_string):
        """Color the edges in the subgraph induced by vertex_id_list
        by color_string."""
        self.edge_set.color_edges_by_id_list(vertex_id_list, color_string)

    def uncolor_edges_by_id_list(self, vertex_id_list):
        """Remove the color of the edges in the subgraph induced
        by vertex_id_list."""
        self.edge_set.uncolor_edges_by_id_list(vertex_id_list)

    def show(self):
        """Print the cube."""
        cube_strings.draw(self)
