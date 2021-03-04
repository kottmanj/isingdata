import tequila as tq
import numpy, json
import yaml
from isingdata import CircuitGenerator, simplified_ising, CircuitGenEncoder

def run_ising_circuits(n_qubits, g=1.0, *args, **kwargs):
    H = simplified_ising(n_qubits=n_qubits, g=g)
    if n_qubits < 10:
        exact_gs = numpy.linalg.eigvalsh(H.to_matrix())[0]
    else:
        exact_gs = None
    
    # orquestra workaround
    if "generators" in kwargs:
        kwargs["generators"] = json.loads(kwargs["generators"])
    if "fix_angles" in kwargs:
        kwargs["fix_angles"] = yaml.load(kwargs["fix_angles"], Loader=yaml.SafeLoader)
    if "connectivity" in kwargs:
        kwargs["connectivity"] = yaml.load(kwargs["connectivity"], Loader=yaml.SafeLoader)

    result_dict = {"schema":"schema"}
    result_dict["data"] = test_circuits(H=H, *args, **kwargs)
    result_dict["kwargs"]=kwargs
    result_dict["g"]=g
    result_dict["exact_ground_state"]=float(exact_gs)
    with open("isingdata.json", "w") as f:
        f.write(json.dumps(result_dict, indent=2))

def test_circuits(H, n_circuits=1, n_trials=1, g=1.0, connectivity="local_line", generators=["Y", "XY", "YZ"], depth=None, **kwargs):
    # initial mean-field like state
    n_qubits = H.n_qubits
    initial_state = sum([tq.gates.Ry(angle=("a", q), target=q) for q in range(n_qubits)],tq.QCircuit())
    print(initial_state)
    # encoder to save circuits as string
    encoder = CircuitGenEncoder()
    # solve "mean field"
    EMF = tq.ExpectationValue(H=H, U=initial_state)
    result = tq.minimize(EMF)
    mfvars = result.variables
    generator = CircuitGenerator(n_qubits=n_qubits, connectivity=connectivity, depth=depth, generators=generators, **kwargs)
    print(generator)
    data = []
    for i in range(n_circuits):
        circuit = initial_state + generator()
        E = tq.ExpectationValue(H=H, U=circuit)
        energy_samples = []
        starting_points = [{k:numpy.random.uniform(0.0,4.0,1)[0]*numpy.pi for k in circuit.extract_variables()} for n in range(n_trials)]
        starting_points = [{k:0.0 for k in circuit.extract_variables()}] + starting_points
        starting_points = [{k:numpy.random.uniform(-0.1,0.1,1)[0]*numpy.pi for k in circuit.extract_variables()}] + starting_points
        for j,variables in enumerate(starting_points):
            print("step {} from {} in circuit {} from {}\n".format(j, len(starting_points), i ,n_circuits))
            variables = {**variables, **mfvars}
            result = tq.minimize(E, initial_values=variables)
            data.append({"energy":result.energy, "variables":{str(k.name):v for k,v in result.variables.items()}, "circuit":encoder(circuit)})
    data = sorted(data, key=lambda x: x["energy"])
    print("finished test_circuits")
    return data

if __name__ == "__main__":
    test_circuits(4)
