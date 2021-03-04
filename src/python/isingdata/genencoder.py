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
                    angle = gate.parameter.extract_variables()
                    if len(angle) == 1:
                        angle = str(angle[0])
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
    def generators(self):
        """
        :return: List of valid generators. Note that ['XY'] and ['YX'] are treated the same
        """
        return self._generators

    @property
    def max_coupling(self):
        """
        :return: Max coupling of qubits through individual gates. E.g max_coupling=2: Only one and two qubit gates will be generated
        """
        return self._max_coupling

    @property
    def max_depth(self):
        """
        :return: Number of gates generated for each circuit
        """
        return  self._max_depth

    def __init__(self, depth:int=None, connectivity: typing.Union[dict, str]=None, n_qubits:int=None, generators:list=None):

        if connectivity is None:
            connectivity = "all_to_all"

        if hasattr(connectivity, "lower"):
            if n_qubits is None:
                raise Exception("need to pass n_qubits if connectivity is automatically generated from key={}".format(connectivity))
            self._connectivity = self.make_connectivity_map(key=connectivity, n_qubits=n_qubits)

        if isinstance(generators, typing.Iterable):
            self._generators = ["".join(sorted(x)).upper() for x in generators]
        elif generators is None:
            self._generators = ["X", "Y", "Z", "XX", "YY", "ZZ", "XY", "XZ", "YZ"]
        else:
            raise Exception("generators should be a list of strings: {}".format(generators))

        if depth is None:
            if n_qubits is None:
                raise Exception("need to pass n_qubits for default value of depth")
            depth = n_qubits
        self._max_depth = depth



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

    def __call__(self):
        return self.make_random_constant_depth_circuit(depth=self.max_depth)

    def make_random_constant_depth_circuit(self, depth):
        connectivity = self.connectivity
        circuit = tq.QCircuit()

        primitives = self.generators
        print(primitives)
        for moment in range(depth):
            qubits = list(connectivity.keys())
            while(len(qubits) > 0):
                try:
                    p = numpy.random.choice(primitives,1)[0]
                    print("picked {} from {}".format(p, primitives))
                    q = numpy.random.choice(qubits,len(p), replace=False)
                    ps = tq.PauliString(data={q[i]:p[i] for i in range(len(p))})
                    print(ps)
                    circuit += tq.gates.ExpPauli(paulistring=str(ps), angle="a{}".format(len(circuit.gates)))
                    qubits = [x for x in qubits if x not in q]
                except ValueError as E:
                    print("failed", "\n", str(E))
                    continue

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
    U3 = encoder.decode(result, variables={"a":1.0})
    print(U3)

    encoder.export_to(circuit=U, filename="before.pdf")
    encoder.export_to(circuit=U2, filename="after.pdf")


    generator = CircuitGenerator(depth=10, connectivity="local_line", n_qubits=5, generators=["Y", "XY"])
    print(generator)
    Urand = generator()
    encoded=encoder(Urand)
    print(encoded)
    encoder.export_to(Urand, filename="random.pdf")




