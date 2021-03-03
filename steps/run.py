import tequila as tq
import numpy, json
from isingdata import CircuitGenerator, simplified_ising, CircuitGenEncoder


def test_circuits(n_qubits, n_circuits=1, n_trials=1, g=1.0, n_gates=None, max_coupling=2, connectivity="local_line", valid_generators=["Y", "XY", "YZ"]):
    initial_state = sum([tq.gates.Ry(angle=("a", q), target=q) for q in range(n_qubits)],tq.QCircuit())
    H = simplified_ising(n_qubits=n_qubits, g=g)
    if n_qubits < 10:
        exact_gs = numpy.linalg.eigvalsh(H.to_matrix())
    else:
        exact_gs = None
    # encoder to save circuits as string
    encoder = CircuitGenEncoder()
    # solve "mean field"
    EMF = tq.ExpectationValue(H=H, U=initial_state)
    result = tq.minimize(EMF)
    mfvars = result.variables
    # add random circuits to mean-field solution and try to minimize from different starting points
    if n_gates is None:
        n_gates = 2*n_qubits
    generator = CircuitGenerator(n_qubits=n_qubits, n_gates=n_gates, connectivity=connectivity, max_coupling=max_coupling, valid_generators=valid_generators)

    data = []
    for i in range(n_circuits):
        circuit = initial_state + generator()
        E = tq.ExpectationValue(H=H, U=circuit)
        energy_samples = []
        starting_points = [{k:numpy.random.uniform(0.0,4.0,1)[0]*numpy.pi for k in circuit.extract_variables()} for n in range(n_trials)]
        starting_points = [{k:0.0 for k in circuit.extract_variables()}] + starting_points
        for variables in starting_points:
            variables = {**variables, **mfvars}
            result = tq.minimize(E, initial_values=variables)
            data.append({"energy":result.energy, "variables":result.variables, "circuit":encoder(circuit)})
    data = sorted(data, key=lambda x: x["energy"])

    result.dict = {"schema":"schema"}
    result.dict["data"] = data
    result.dict["n_qubits"]=n_qubits
    result.dict["n_circuits"]=n_circuits
    result.dict["n_trials"]=n_trials
    result.dict["g"]=g
    result.dict["exact_ground_state"]=exact_gs
    with open("isingdata.json", "w") as f:
        f.write(json.dumps(result_dict, indent=2))

