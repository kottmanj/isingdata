"""
Generator Based Encoding For Quantum Circuits
"""

import tequila as tq
import numpy, typing, numbers

class CircuitGenEncoder:

    symbols = {"gate_separator":"|", "angle_separator":"@"}

    def __call__(self, circuit:typing.Union[tq.QCircuit, str], *args, **kwargs):
        if hasattr(circuit, "gates") or isinstance(circuit, tq.QCircuit):
            return self.encode(circuit=circuit, *args, **kwargs)
        elif hasattr(circuit, "lower" or isinstance(circuit, str)):
            return self.decode(string=circuit, *args, **kwargs)
        else:
            raise Exception("unexpected input type for circuit: {}\n{}".format(type(circuit), circuit))

    def compile(self, circuit):
        # need to compile Hadamard gates
        # take over to tq compiler at some point
        compiled = []
        for gate in circuit.gates:
            if gate.name.lower() == "h":
                angle = gate.parameter if hasattr(gate, "parameter") else 1.0
                decomposed = tq.QCircuit()
                decomposed += tq.gates.Ry(angle=-numpy.pi / 4, target=gate.target)
                decomposed += tq.gates.Rz(angle=angle*numpy.pi, target=gate.target, control=gate.control)
                decomposed += tq.gates.Ry(angle=numpy.pi / 4, target=gate.target)
                compiled += decomposed.gates
            else:
                compiled.append(gate)

        return tq.QCircuit(gates=compiled)

    def encode(self, circuit, variables: dict=None):
        circuit = self.compile(circuit)
        result = ""
        for gate in circuit.gates:
            generator = gate.make_generator(include_controls=True)
            if hasattr(gate, "parameter"):
                try:
                    angle = gate.parameter(variables)
                except:
                    angle = gate.parameter
            else:
                angle = 1.0
            for ps in generator.paulistrings:
                if len(ps) == 0:
                    # ignore global phases
                    continue
                else:
                    result += self.encode_paulistring(ps=ps, angle=angle)

        return result

    def decode(self, string:str, variables:dict=None):
        string_gates = string.split(self.symbols["gate_separator"])
        circuit = tq.QCircuit()
        for gate in string_gates:
            gate = gate.strip()
            if gate=="":
                continue
            angle, gate = gate.split(self.symbols["angle_separator"])
            try:
                angle=float(angle)
            except:
                angle = angle.strip()
                if angle == "":
                    angle=1.0
                elif variables is not None and angle in variables:
                    angle = variables[angle]
            ps = self.decode_paulistring(input=gate)
            circuit += tq.gates.ExpPauli(paulistring=ps, angle=angle)
        return circuit

    def encode_paulistring(self, ps, angle=1.0):
        if isinstance(angle, numbers.Number):
            local_angle = ps.coeff * angle% (2.0 * numpy.pi)
            angle = ""
        else:
            local_angle = ps.coeff % (2.0 * numpy.pi)

        gen_string = str(ps.naked())
        return "{}{}{:2.4f}{}{}".format(angle, self.symbols["angle_separator"], local_angle, gen_string, self.symbols["gate_separator"])

    def decode_paulistring(self, input) -> tq.QubitHamiltonian:
        ps = tq.QubitHamiltonian.from_string(input)
        assert len(ps) == 1
        return ps.paulistrings[0]

    def export_to(self, circuit, filename="circuit.pdf"):
        tq.circuit.export_to(self.compile(circuit), filename=filename, always_use_generators=True, decompose_control_generators=True)

class CircuitGenerator:

    @property
    def n_qubits(self):
        """
        :return: The number of qubits in the generated circuits
        """
        return len(self.qubits)

    @property
    def qubits(self):
        """
        :return: The qubit labels in the generated circuits
        """
        return list(self.connectivity.keys())

    @property
    def connectivity(self):
        """
        :return: The connectivity of the generated circuits
        """
        return self._connectivity

    @property
    def valid_generators(self):
        """
        :return: List of valid generators. Note that ['XY'] and ['YX'] are treated the same
        """
        return self._valid_generators

    @property
    def max_coupling(self):
        """
        :return: Max coupling of qubits through individual gates. E.g max_coupling=2: Only one and two qubit gates will be generated
        """
        return self._max_coupling

    @property
    def n_gates(self):
        """
        :return: Number of gates generated for each circuit
        """
        return  self._n_gates

    def __init__(self, n_gates:int, connectivity: typing.Union[dict, str]=None, n_qubits:int=None, valid_generators:list=None, max_coupling:int=2):

        self._n_gates = n_gates

        if connectivity is None:
            connectivity = "all_to_all"

        if hasattr(connectivity, "lower"):
            if n_qubits is None:
                raise Exception("need to pass n_qubits if connectivity is automatically generated from key={}".format(connectivity))
            self._connectivity = self.make_connectivity_map(key=connectivity, n_qubits=n_qubits)

        if isinstance(valid_generators, typing.Iterable):
            self._valid_generators = ["".join(sorted(x)).upper() for x in valid_generators]
        else:
            self._valid_generators=valid_generators

        assert max_coupling is not None
        self._max_coupling = max_coupling

    def make_connectivity_map(self, key:typing.Union[str,tq.QCircuit], n_qubits:int=None):
        if hasattr(key, "lower"):
            if n_qubits is None:
                raise Exception("make_connectivity_map from key needs n_qubits")
            if key.lower() == "all_to_all":
                return {k:[l for l in range(n_qubits) if l != k] for k in range(n_qubits)}
            elif key.lower() == "local_line":
                return {0:[1],**{k:[k+1,k-1] for k in range(1,n_qubits-1)}, n_qubits:[n_qubits-1]}
            elif key.lower() == "local_ring":
                return {k:[(k+1)%n_qubits,(k-1)%n_qubits] for k in range(n_qubits)}
            else:
                raise Exception("unknown key to create connectivity_map: {}".format(key))
        else:
            return self.make_connectivity_map_from_circuit(circuit=key)

    @staticmethod
    def make_connectivity_map_from_circuit(circuit:tq.QCircuit):
        raise NotImplementedError("still missing")

    def is_valid(self, ps : tq.PauliString):
        if hasattr(ps, "paulistrings"):
            assert len(ps)==1
            ps = ps.paulistrings[0]

        if self.valid_generators is None:
            return True
        elif isinstance(self.valid_generators, typing.Iterable):
            return "".join(sorted(ps.values())).upper() in self.valid_generators
        elif isinstance(self.valid_generators, typing.Callable):
            return self.valid_generators(ps)
        else:
            raise Exception("self.valid_generators needs to be a list or a function.\n{}".format(self.valid_generators))

    def __call__(self):
        connectivity = self.connectivity
        primitives = ["X", "Y", "Z"]
        circuit = tq.QCircuit()
        while(len(circuit.gates) < self.n_gates):
            p0 = numpy.random.choice(primitives,1)[0]
            q0 = int(numpy.random.choice(list(connectivity.keys()),1))
            ps_string = "{}({})".format(p0, q0)
            for j in range(self.max_coupling-1):
                q1 = int(numpy.random.choice(connectivity[q0],1))
                tmp = "{}({})".format(numpy.random.choice(primitives+["I"], 1)[0], q1)
                if "I" not in tmp:
                    ps_string += tmp
            ps = tq.PauliString.from_string(ps_string)
            if not self.is_valid(ps):
                continue
            circuit += tq.gates.ExpPauli(paulistring=ps, angle=(len(circuit.gates),))
        return circuit

    def __repr__(self):
        result = "CircuitGenerator\n"
        result += "{:30} : {}\n".format("n_qubits", self.n_qubits)
        result += "{:30} : {}\n".format("qubits", self.qubits)
        for k,v in self.__dict__.items():
            result += "{:30} : {}\n".format(k, v)

        return result

def prune_circuit(circuit, variables, threshold=1.e-4):
    gates = []
    for gate in circuit.gates:
        if hasattr(gate, "parameter"):
            angle = (gate.parameter(variables)%(2.0*numpy.pi))
            if not numpy.isclose(angle, 0.0, atol=threshold):
                gates.append(gate)
        else:
            gates.append(gate)
    if len(gates) != len(circuit.gates):
        print("pruned from {} to {}".format(len(circuit.gates), len(gates)))
    return tq.QCircuit(gates=gates)


if __name__ == "__main__":

    U = tq.gates.X(0) + tq.gates.H(0) + tq.gates.Ry(target=1, angle="a")
    encoder = CircuitGenEncoder()
    result = encoder(U)
    print(result)
    U2 = encoder.decode(result)
    print(U2)

    encoder.export_to(circuit=U, filename="before.pdf")
    encoder.export_to(circuit=U2, filename="after.pdf")

    # example: only ZZ as two-qubit gate
    def all_single_and_zz(ps):
        if len(ps) ==1:
            return True
        elif len(ps) ==2 and list(ps.values()).count("Z") == 2:
            return True
        else:
            return False

    # example: only number conserving two qubit gates
    # circuit is not necesarily number conserving, but has the necessary gates
    # would be the job of the AI algorithm to figure out that for each XY we also need a YX
    def only_xy(ps):
        if len(ps) ==2 and list(ps.values()).count("X") == list(ps.values()).count("Y"):
            return True
        else:
            return False

    generator = CircuitGenerator(n_gates=10, connectivity="local_line", n_qubits=5, valid_generators=["XY"])
    print(generator)
    Urand = generator()
    encoder.export_to(Urand, filename="random.pdf")




