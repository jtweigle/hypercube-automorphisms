"""An environment for visualizing what quantum circuits do to
multi-cubit states, using ascii art.

"""

import bits
import numpy as np
from cube_repl import CubeRepl, CubeError
from qiskit import QuantumCircuit, Aer, assemble
from colorama import Fore, Back, Style

STATEVECTOR_SIMULATOR = Aer.get_backend("statevector_simulator")

GRAMMAR = r'''
        @@ignorecase::True
        @@grammar::Commands
    
        start = { command }+ $ ;
        
        command
        =
        | 'circuit' dimension
        | 'add' gate
        | 'back'
        | 'reset'
        | 'help'
        | 'exit'
        | 'verbose'
        ;

        dimension = nat ;
        gate
        =
        | 'x' nat
        | 'y' nat
        | 'z' nat
        | 'h' nat
        | 't' nat
        | 'tdg' nat
        | 's' nat
        | 'sdg' nat
        | 'i' nat
        | 'cx' nat nat
        ;

        nat = /[0-9]+/;

        '''

class CircuitRepl:
    """A CubeRepl used for representing statevectors of quantum circuits."""
    def __init__(self):
        self.cube_repl = CubeRepl(GRAMMAR)
        # The repl starts with Q0, but I want to show a message instead.
        self.cube_repl.cube.show = lambda : print("\n\nNo circuit yet. "
                                                  + "Try 'help' for usage."
                                                  + "\n\n")

        self.cube_repl.add_before_drawing_hook(self.show_circuit)
        self.cube_repl.add_before_drawing_hook(self.update_statevector)
        self.cube_repl.add_before_drawing_hook(self.color_vertices)
        self.cube_repl.add_after_drawing_hook(self.show_color_key)

        self.circuit      = None
        self.statevector = None

        self.color_key = {
            0.00 : "",
            0.05 : Fore.MAGENTA,
            0.10 : Fore.BLUE,
            0.15 : Fore.GREEN,
            0.20 : Fore.YELLOW,
            0.25 : Fore.RED,
            0.30 : Back.MAGENTA,
            0.35 : Back.BLUE,
            0.40 : Back.GREEN,
            0.45 : Back.YELLOW,
            0.50 : Back.RED,
            0.55 : Fore.MAGENTA + Style.BRIGHT,
            0.60 : Fore.BLUE + Style.BRIGHT,
            0.65 : Fore.GREEN + Style.BRIGHT,
            0.70 : Fore.YELLOW + Style.BRIGHT,
            0.75 : Fore.RED + Style.BRIGHT,
            0.80 : Back.MAGENTA + Style.BRIGHT,
            0.85 : Back.BLUE + Style.BRIGHT,
            0.90 : Back.GREEN + Style.BRIGHT,
            0.95 : Back.YELLOW + Style.BRIGHT,
            1.00 : Back.RED + Style.BRIGHT,
            }

        self.cube_repl.add_command("circuit", "Make a new circuit.",
                                   ["circuit 4"], self.new_circuit)
        self.cube_repl.add_command("back", "Remove the last-added gate.",
                                   ["back"], self.back)
        self.cube_repl.add_command("add", "Add a circuit.",
                                   ["add cx 0 2",
                                    "add x 1",
                                    "add y 2",
                                    "add z 0",
                                    "add h 3",
                                    "add t 4",
                                    "add tdg 4",
                                    "add s 2",
                                    "add sdg 2",
                                    "add i 0"], self.add)

    def new_circuit(self):
        """Replace `circuit` with a new quantum circuit, with the number
        of qubits given in `self.cube_repl.arguments[0]`.

        """
        try:
            dimension_str = self.cube_repl.arguments[0]
        except IndexError as e:
            raise CubeError("Unable to read the number of qubits.") from e
        dimension = int(dimension_str)

        if dimension < 1:
            raise CubeError("There must be at least 1 qubit.")
        self.circuit = QuantumCircuit(dimension)

        self.cube_repl.new_cube()

    def update_statevector(self):
        """Update `self.statevector` to match `self.circuit`."""
        if self.circuit is not None:
            qobj = assemble(self.circuit)
            result = STATEVECTOR_SIMULATOR.run(qobj).result()
            self.statevector = result.get_statevector()


    def back(self):
        """Pops the last used gate off `self.circuit`."""
        try:
            self.circuit.data.pop()
        except IndexError as e:
            raise CubeError("We can't go any further back!") from e

    def add(self):
        """Add a gate to the circuit."""
        args = self.cube_repl.arguments[0]
        gate_type = args[0]
        dimension = self.cube_repl.cube.dimension

        if gate_type == "cx":
            indices      = args[1:]
            first_index  = int(indices[0])
            second_index = int(indices[1])

            if first_index == second_index:
                raise CubeError("Indices must be distinct.")
            first_in_range = first_index in range(dimension)
            second_in_range = second_index in range(dimension)
            if not first_in_range or not second_in_range:
                raise CubeError(f"Indices must be less than {dimension}.")
            self.circuit.cx(first_index, second_index)
            return

        index = int(args[1])
        if index not in range(dimension):
            raise CubeError(f"Indices must be less than {dimension}.")

        if gate_type == "x":
            self.circuit.x(index)
            return
        if gate_type == "y":
            self.circuit.y(index)
            return
        if gate_type == "z":
            self.circuit.z(index)
            return
        if gate_type == "h":
            self.circuit.h(index)
            return
        if gate_type == "s":
            self.circuit.s(index)
            return
        if gate_type == "sdg":
            self.circuit.sdg(index)
            return
        if gate_type == "t":
            self.circuit.t(index)
            return
        if gate_type == "tdg":
            self.circuit.tdg(index)
            return
        if gate_type == "i":
            self.circuit.i(index)
            return

    def show_circuit(self):
        """Print `self.circuit` if it exists."""
        if self.circuit is not None:
            print(self.circuit)

    def show_color_key(self):
        """Print `self.color_key` if there's a circuit.
        """
        if self.circuit is None: return
        string = ""
        for probability, color_string in self.color_key.items():
            string = string + color_string + str(probability) + Style.RESET_ALL
            string = string + " "
        print("Probabilities rounded to the nearest 0.05:")
        print(string)

    def color_vertices(self):
        """Update `self.cube_repl.cube`, coloring the vertices according
        to the probability of the system getting measured in that
        state.
        
        """
        if self.statevector is None: return
        def get_color_string(coefficient):
            coefficient = np.round(coefficient, 2)
            probability = abs(coefficient) * abs(coefficient)
            rounded_probability = round(probability * 2, 1) / 2.0
            if rounded_probability > 1 or rounded_probability < 0:
                raise CubeError("The probability was undefined.")
            return self.color_key[rounded_probability]

        for outcome, coefficient in enumerate(self.statevector):
            vertex_id = bits.reverse(outcome, self.cube_repl.cube.dimension)
            color_string = get_color_string(coefficient)
            self.cube_repl.cube.color_vertices_by_id_list([vertex_id],
                                                          color_string)

    def run(self):
        self.cube_repl.run()

if __name__ == "__main__":
    circuit_repl = CircuitRepl()
    circuit_repl.run()
