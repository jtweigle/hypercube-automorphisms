"""A REPL environment in which you can create and play with
hypercubes."""

from cubes import Cube
from colorama import Fore, Back
from tatsu import compile as compile_parser, exceptions
import bits

# User commands in the repl environment are defined by the
# following grammar:
GRAMMAR = r'''
        @@ignorecase::True
        @@grammar::Commands
    
        start = { command }+ $ ; # always a list
        
        command
        =
        | 'new' dimension
        | 'color' coloroptions color
        | 'uncolor' coloroptions
        | 'reflect' bitstring
        | 'rotate' rotationlist
        | 'reset'
        | 'help'
        | 'exit'
        | 'verbose'
        ;

        coloroptions
        =
        | 'between' vertices            # (un)color edges in Q[vertices]
        | 'subcube' inducedvertexstring # (un)color both vertices and edges
        | vertices                      # (un)color vertices
        ;
        
        rotationlist = { nat }+ ;
        dimension = nat ;

        bitstring = /[01]+/ ;
        nat = /[0-9]+/;

        vertices 
         =
         | inducedvertexstring
         | { vertex }+ 
         ;
        
        vertex = bitstring ;
        inducedvertexstring = /[*01]*\*[*01]*/ ; # at least one star
        
        color
        =
        | 'red'
        | 'blue'
        | 'green'
        | 'yellow'
        | 'white'
        | 'black'
        | 'magenta'
        | 'cyan'
        ;

        '''

class CubeError(Exception):
    """User-friendly error messages, meant to appear in the CubeRepl
    if `verbose` is turned on.

    """
    def __init__(self, message="That command failed!"):
        self.message = message
        super().__init__(self.message)

class CubeRepl:
    """A REPL environment for playing with hypercube automorphisms."""
    def __init__(self, grammar=None):
        self.known_commands = dict()

        if grammar is None:
            self.command_parser = compile_parser(GRAMMAR)
        else:
            self.command_parser = compile_parser(grammar)

        self.command = "help"
        self.command_list = ["help"]
        self.arguments = []
        self.exit = False
        self.verbose = False
        self.cube = Cube(0)
        # functions to execute before and after drawing the cube
        self.before_drawing_hooks = []
        self.after_drawing_hooks  = []

        # Obligatory commands
        self.add_command("help", "Print a help message.", "help",
                         self.print_help)
        self.add_command("exit", "Quit.", "exit",
                         self.exit_command)
        self.add_command("verbose", "Turn on verbose mode for more detail.",
                         "verbose", self.toggle_verbose)

        if grammar is None:
            # Less obligatory commands
            self.add_command("new", "Create a new cube of the given dimension.",
                             "new", self.new_cube)
            self.add_command("reflect", "Reflect the cube by flipping bits.",
                             "reflect 011101", self.reflect)
            self.add_command("rotate", "Rotate the cube by permuting bits.",
                             "rotate 3 1 2 0", self.rotate)
            self.add_command("reset", "Reset the positions of all vertices.",
                             "reset", self.reset_positions)
            self.add_command("color", "Color some element of the cube.",
                             "color 1010 red", self.color)
            self.add_command("uncolor", "Uncolor some element of the cube.",
                             "uncolor 1****", self.uncolor)

    def run(self):
        """Run the REPL."""
        while not self.exit:

            self.behavior_at_iteration()

            user_input = input("> ")
            if user_input == "":
                try:
                    self.execute_previous_command_list()
                except CubeError as e:
                    self.print_cube_error(e)
                continue
            try:
                self.command_list = self.command_parser.parse(user_input,
                                                         rule_name="start")
            except exceptions.FailedParse:
                print("Hm, that command didn't match my command grammar. "
                      "Try 'help', I guess?")
            else:
                try:
                    self.execute_command_list(self.command_list)
                except CubeError as e:
                    self.print_cube_error(e)

    def behavior_at_iteration(self):
        """Execute this during every iteration of the REPL."""
        for before_function in self.before_drawing_hooks:
            before_function()

        self.cube.show()

        for after_function in self.after_drawing_hooks:
            after_function()

    def add_before_drawing_hook(self, function_to_call):
        """Execute `function_to_call` before printing the cube."""
        self.before_drawing_hooks.append(function_to_call)

    def add_after_drawing_hook(self, function_to_call):
        """Execute `function_to_call` after printing the cube."""
        self.after_drawing_hooks.append(function_to_call)

    # ======================
    # HANDLING USER COMMANDS
    # ======================

    def add_command(self, command_name, description,
                    example,
                    function_to_execute):
        """Add `command_name` to the dictionary `self.known_commands`,
        with the value

        (`description`, # a string describing the function's behavior
         `example`,     # an example of usage
         `function_to_execute`).

        If a function needs arguments, it takes them from
        `self.arguments`.

        """
        self.known_commands[command_name] = (description,
                                             example,
                                             function_to_execute)

    def update_command_and_arguments(self, command_tree):
        """Update `self.command` and `self.arguments` with the given
        `command_tree`.

        The parser returns either a string (for a singleton command)
        or a list, where the first element is the command name
        and the rest is an argument list.

        """
        if command_tree is None:
            raise CubeError("No command given.")
        if isinstance(command_tree, str):
            command_name = command_tree
            arguments = []
        else:
            try:
                command_name = command_tree[0]
                arguments = command_tree[1:]
            except IndexError:
                #pylint: disable=raise-missing-from
                raise CubeError("Unable to access the arguments.")

        self.command = command_name
        self.arguments = arguments

    def execute_command(self, command_tree):
        """Attempt to execute the given `command_tree`, which
        is either a string or a list of strings.

        If command_tree is `None`, execute self.command.

        """
        if command_tree is not None:
            self.update_command_and_arguments(command_tree)

        description_example_function = self.known_commands.get(self.command,
                                                               None)
        if description_example_function is None:
            raise CubeError("I don't know that command yet.")
        function = description_example_function[2]
        function()

    def execute_command_list(self, command_list):
        """Attempt to execute the list of commands
        in `command_list`.

        """
        for command in command_list:
            self.execute_command(command)

    def execute_previous_command_list(self):
        """Execute the previous list of commands."""
        self.execute_command_list(self.command_list)

    def print_help(self):
        """Print known_commands in a helpful way."""
        for key, value in self.known_commands.items():
            print(f"{key}: {value[0]}")
            print(f"  Example usage: {value[1]}")
        print("You can put more than one command together in a line."
              + "\n  Example: command1 command2 command3")
        print("Hit enter to repeat the previous list of commands.")

    def toggle_verbose(self):
        """Turn verbose mode on or off."""
        self.verbose = not self.verbose
        if self.verbose:
            print("Verbose is on.")

    def exit_command(self):
        """Quit."""
        self.exit = True

    def new_cube(self):
        """Make a new cube with a dimension given in `self.arguments`."""
        dimension = int(self.arguments[0])
        self.cube = Cube(dimension)

    def print_cube_error(self, error):
        """Print the error if `self.verbose` is `True`."""
        if self.verbose:
            print(error.message)

    # ==================
    # MODIFYING THE CUBE
    # ==================

    def reflect(self):
        """Reflect `self.cube` with a reflection string given in
        `self.arguments`.

        """
        if self.cube.dimension == 0:
            raise CubeError("You can't reflect a zero-dimensional cube!")
        bit_string = self.arguments[0]

        if len(bit_string) != self.cube.dimension:
            raise CubeError("Bit string is the wrong length.")
        try:
            bit_mask = bits.bit_string_to_int(bit_string)
        except ValueError:
            #pylint: disable=raise-missing-from
            #reason: user-friendly command
            raise CubeError("The bit string should be a string of 1 and 0. "
                            + "Try 'help' for usage.")

        self.cube.reflect(bit_mask)

    def rotate(self):
        """Rotate `self.cube` with a rotation list given in
        `self.arguments`.

        This is a list of indices given as strings.

        """
        if self.cube.dimension == 0:
            raise CubeError("That's not going to do anything.")
        rotation_list = self.arguments[0]

        indices = list(map(int, rotation_list))
        dimension = self.cube.dimension
        def is_valid_rotation_list(indices):
            """Verify that the list of indices in fact specifies a
            permutation.

            """
            if len(indices) != dimension:
                return False
            if not all([i in indices for i in range(dimension)]):
                return False
            return True

        if not is_valid_rotation_list(indices):
            raise CubeError(message="Rotation list should contain "
                            + f"all indices from 0 to {dimension - 1}, "
                            + "and nothing else.")

        self.cube.rotate(indices)

    def reset_positions(self):
        """Reset the position of all vertices in `self.cube`,
        but preserve colors.

        """
        self.cube.reset_positions()

    def get_color_string_for_vertices(self, color_name):
        """Return the color string corresponding to `color_name`,
        good for coloring vertices.

        """
        colors = {
            "red"     : Back.RED,
            "blue"    : Back.BLUE,
            "green"   : Back.GREEN,
            "yellow"  : Back.YELLOW,
            "white"   : Back.WHITE + Fore.BLACK,
            "black"   : Back.BLACK + Fore.WHITE,
            "magenta" : Back.MAGENTA,
            "cyan"    : Back.CYAN,
            ""        : ""
        }

        color_string = colors.get(color_name, None)

        if color_string is None:
            raise CubeError("Sorry, I haven't implemented that color "
                            +"for vertices.")

        return color_string

    def get_color_string_for_edges(self, color_name):
        """Return the color string corresponding to `color_name`,
        good for coloring edges.

        """
        colors = {
            "red"     : Fore.RED,
            "blue"    : Fore.BLUE,
            "green"   : Fore.GREEN,
            "yellow"  : Fore.YELLOW,
            "white"   : Fore.WHITE + Back.BLACK,
            "black"   : Fore.BLACK + Back.WHITE,
            "magenta" : Fore.MAGENTA,
            "cyan"    : Fore.CYAN,
            ""        : ""
        }

        color_string = colors.get(color_name, None)

        if color_string is None:
            raise CubeError("Sorry, I haven't implemented that color "
                            +"for edges.")

        return color_string

    def uncolor(self):
        """Uncolor some element of `self.cube`.

        `self.arguments[0]` specifies the options for which
         elements to color, in the same manner as `self.color`.

        """
        color_options = self.arguments[0]
        color_string = ""
        self.arguments = (color_options, color_string)
        self.color()

    def color_vertices_by_id_list(self, vertex_id_list, color_string):
        """Color the given vertices in `self.cube` with color_string.

        """
        if self.cube.dimension == 0:
            self.cube.color_vertices_by_id_list([0], color_string)
        self.cube.color_vertices_by_id_list(vertex_id_list, color_string)

    def color_edges_by_id_list(self, vertex_id_list, color_string):
        """Color the edges by `color_string` in the subgraph induced by
        `vertex_id_list`.

        """
        try:
            self.cube.color_edges_by_id_list(vertex_id_list, color_string)
        except ValueError as e:
            raise CubeError("Unable to color the edges.") from e

    def read_vertex_list(self, vertex_string_list):
        """Return a list of vertex ids corresponding to
        `vertex_string_list`, or raise a CubeError.

        """
        try:
            vertex_list = bits.strings_to_int_list(vertex_string_list,
                                                   self.cube.dimension)
        except ValueError as e:
            raise CubeError("Unable to read the vertex list. "
                            + "Make sure each vertex has length "
                            + f"{self.cube.dimension}.") from e
        return vertex_list

    def read_vertex_pattern(self, vertex_pattern):
        """Return a list of vertex ids that match `vertex_pattern`, which
        is a bit string with a wildcard character `*`.

        """
        try:
            vertex_list = bits.pattern_to_int_list(vertex_pattern,
                                                   self.cube.dimension)
        except ValueError as e:
            raise CubeError("Unable to read the pattern string. "
                            + "Make sure it has length "
                            + f"{self.cube.dimension}.") from e
        return vertex_list

    def read_vertex_specifier(self, vertex_specifier):
        """Return a list of vertex ids from the `vertex_specifier`, which
        is either a list of vertex_ids as strings, or a bit
        string with a wildcard character `*`.

        """
        if vertex_specifier is None:
            return []
        if isinstance(vertex_specifier, str):
            return self.read_vertex_pattern(vertex_specifier)
        return self.read_vertex_list(vertex_specifier)

    def color(self):
        """Color some element of `self.cube`.

        The first, argument, `color_options`, is one of the
        following:
        - A specifier of a vertex set, which is either:
          - a pattern string that induces a vertex set (like `*100**1`).
          - a list of vertex ID strings.

        - A tuple `("between", S)` for a vertex set specified by `S`.

          This means we color the edges in the subgraph induced by that
          vertex set.

        - A tuple `("subcube", pattern_string)` for a pattern string (like
          `*10*****1`).

          This means we color both vertices and edges matching the pattern.

        """
        color_options = self.arguments[0]
        color_name = self.arguments[1]
        vertex_color = self.get_color_string_for_vertices(color_name)

        if self.cube.dimension == 0:
            if color_options == "between":
                return
            self.color_vertices_by_id_list([0], vertex_color)
            return

        edge_color = self.get_color_string_for_edges(color_name)

        if isinstance(color_options, str):
            # must be a vertex pattern.
            vertex_id_list = self.read_vertex_pattern(color_options)
            self.color_vertices_by_id_list(vertex_id_list, vertex_color)
            return

        if color_options[0] == "between":
            vertex_id_list = self.read_vertex_specifier(color_options[1])
            self.color_edges_by_id_list(vertex_id_list, edge_color)
            return

        if color_options[0] == "subcube":
            vertex_id_list = self.read_vertex_pattern(color_options[1])
            self.color_edges_by_id_list(vertex_id_list, edge_color)
            self.color_vertices_by_id_list(vertex_id_list, vertex_color)
            return

        # Here we know it has to be a vertex list.
        vertex_id_list = self.read_vertex_list(color_options)
        self.color_vertices_by_id_list(vertex_id_list, vertex_color)


if __name__ == "__main__":
    repl = CubeRepl(None)
    repl.run()
