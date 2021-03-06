import tequila as tq
import numpy, json
import yaml
from isingdata import simplified_ising
from genencoder import CircuitGenerator, CircuitGenEncoder

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
    
    # initial mean-field like state
    n_qubits = H.n_qubits
    UMF = sum([tq.gates.Ry(angle=("a", q), target=q) for q in range(n_qubits)],tq.QCircuit())
    # encoder to save circuits as string
    encoder = CircuitGenEncoder()
    # solve "mean field"
    EMF = tq.ExpectationValue(H=H, U=UMF)
    result = tq.minimize(EMF)

    result_dict = {"schema":"schema"}
    result_dict["data"] = test_circuits(H=H, UMF=UMF, mf_variables=result.variables, *args, **kwargs)
    result_dict["kwargs"]=kwargs
    result_dict["g"]=g
    result_dict["exact_ground_state"]=exact_gs
    result_dict["mean_field_energy"]=float(result.energy)
    with open("isingdata.json", "w") as f:
        f.write(json.dumps(result_dict, indent=2))

def test_circuits(H, UMF, mf_variables, n_circuits=1, n_trials=1, n_samples=1000, g=1.0, connectivity="local_line", generators=["Y", "XY", "YZ"], depth=None, fix_mean_field=True, only_samples=False, draw_from_normal_distribution=False, **kwargs):
    # initial mean-field like state
    n_qubits = H.n_qubits
    # encoder to save circuits as string
    encoder = CircuitGenEncoder()
    if fix_mean_field:
        fixed_variables = mf_variables
    else:
        fixed_variables = {}

    generator = CircuitGenerator(n_qubits=n_qubits, connectivity=connectivity, depth=depth, generators=generators, **kwargs)
    print(generator)
    data = []
    for i in range(n_circuits):
        circuit = UMF + generator()
        E = tq.ExpectationValue(H=H, U=circuit)
        E = tq.compile(E, backend="qulacs")
        sampled_energies = []
        sampled_variables = []
        for sample in range(n_samples):
            if draw_from_normal_distribution:
                variables = {k:numpy.random.normal(loc=1.0, scale=1.0)*numpy.pi for k in circuit.extract_variables()}
            else:
                variables = {k:numpy.random.uniform(0.0,4.0,1)[0]*numpy.pi for k in circuit.extract_variables()}

            variables = {**variables, **fixed_variables}
            sampled_energies.append(E(variables=variables))
            sampled_variables.append(variables)
        
        best_variables = sorted( [(sampled_energies[i],sampled_variables[i]) for i in range(n_samples)]  , key=lambda x:x[0] )
        best_variables = [best_variables[i][1] for i in range(n_trials)]
        starting_points = best_variables 
        starting_points = [{k:0.0 for k in circuit.extract_variables()}] + starting_points
        starting_points = [{k:numpy.random.uniform(-0.1,0.1,1)[0]*numpy.pi for k in circuit.extract_variables()}] + starting_points
        ev_samples = []
        encoded_circuit = encoder(circuit, variables=fixed_variables)
        if not only_samples:
            for j,variables in enumerate(starting_points):
                print("step {} from {} in circuit {} from {}\n".format(j, len(starting_points), i ,n_circuits))
                variables = {**variables, **fixed_variables}
                active_variables = [x for x in E.extract_variables() if x not in fixed_variables.keys()]
                E = tq.ExpectationValue(H=H, U=circuit)
                result = tq.minimize(E, initial_values=variables, variables=active_variables)
                variables = result.variables
                energy = result.energy
                ev_samples.append({"energy":energy, "variables":{str(k):v for k,v in variables.items()} })
            energy_samples={"circuit":encoded_circuit, "vqe_energies": sorted(ev_samples, key=lambda x: x["energy"]), "random_energies":sampled_energies}
            data.append(energy_samples)
            data = sorted(data, key=lambda x: x["vqe_energies"][0]["energy"])
        else:
            zeroes={k:0.0 for k in E.extract_variables()}
            energy_samples={"circuit":encoded_circuit, "vqe_energies": [{"energy":tq.simulate(E, variables=zeroes), "variables":{str(k):v for k,v in zeroes.items()}}], "random_energies":sampled_energies}
            data.append(energy_samples)
    
    print("finished test_circuits")
    return data

if __name__ == "__main__":
    test_circuits(4)
