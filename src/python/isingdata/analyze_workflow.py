import json
import tequila as tq
from genencoder import CircuitGenEncoder
import matplotlib.pyplot as plt

def average(x):
    return sum(x)/len(x)

def analyze_workflow(filename="workflow_result.json"):
    encoder = CircuitGenEncoder()
    
    data = None
    with open(filename, 'r') as myfile:
        data=myfile.read()
    data = json.loads(data)
    print(type(data))
    
    n_steps = len(data)
    
    isingdata = []
    exact = None
    mf_energy = None
    n_qubits = None
    kwargs = None
    generators = None
    g = None
    for k1,v1 in data.items():
        isingdata += v1["isingdata"]["data"] # this is a list of dictionaries with circuit and vqe_energies, we're collecting all of them in a big list
        gs_energy = v1["isingdata"]["exact_ground_state"]
        mf_energy = v1["isingdata"]["mean_field_energy"]
        kwargs = v1["isingdata"]["kwargs"]
        g = v1["isingdata"]["g"]
        print(gs_energy)
        exact=gs_energy
    if kwargs is None:
        kwargs = {}
    if "generators" in kwargs:
        generators = kwargs["generators"]
    if generators is None:
        generators = "['Y', 'XY', 'YZ']"
    
    # sort by best samples/optimizations
    isingdata = sorted(isingdata, key=lambda x: min([ y["energy"] for y in x["vqe_energies"] ]))
    all_energies = []
    best_energies = []
    energies = []
    random_energies=[]
    min_max_random_energies = [] # only minimum/maximum and average of random_energies
    best_vqe = []
    best_sample = []
    for x in isingdata:
        all_energies += [float(y["energy"]) for y in x["vqe_energies"]]
        best_energies+= [float(x["vqe_energies"][0]["energy"])] # best energy samples for each circuit extracted
        best_vqe+= [float(x["vqe_energies"][0]["energy"])] # best energy samples for each circuit extracted
        best_sample+= [float(min(x["random_energies"]))] # best energy samples for each circuit extracted
        energies.append([float(y["energy"]) for y in x["vqe_energies"]]) # all vqe_energies grouped for each circuit
        random_energies.append([float(y) for y in x["random_energies"]]) # all randomly sampled energies grouped for each circuit
        min_max_random_energies.append([min(x["random_energies"]), max(x["random_energies"]), average(x["random_energies"])]) # all randomly sampled energies grouped for each circuit

    names_energies=[]
    names_energies_worst=[]
    n_qubits = 0
    for i,x in enumerate(isingdata):
        # energy samples are sorted in the workflow
        U = encoder.prune_circuit(encoder(x["circuit"]),variables=x["vqe_energies"][0]["variables"])
        n_qubits = max(n_qubits,U.n_qubits)
        name = "circuit_{}.pdf".format(i)
        tq.circuit.export_to(U, filename=name)
        names_energies += [(name, x["vqe_energies"][0]["energy"])]
        if i>4:
            break
    for i,x in enumerate(reversed(isingdata)):
        # energy samples are sorted in the workflow
        U = encoder.prune_circuit(encoder(x["circuit"]),variables=x["vqe_energies"][0]["variables"])
        n_qubits = max(n_qubits,U.n_qubits)
        name = "worst_circuit_{}.pdf".format(i)
        tq.circuit.export_to(U, filename=name)
        names_energies_worst += [(name, x["vqe_energies"][0]["energy"])]
        if i>4:
            break
 
    print("exact ground state energy", exact)
    fig=plt.figure()
    plt.plot(all_energies, label="all_energies", color="navy")
    if exact is not None: plt.axhline(y=exact, color="tab:red", label="exact ground state")
    plt.axhline(y=mf_energy, color="tab:green", label="mean-field")
    plt.legend()
    fig.savefig("all_energies.png")
    fig=plt.figure()
    plt.plot(best_energies, label="best energies", color="navy")
    if exact is not None: plt.axhline(y=exact, color="tab:red", label="exact ground state")
    plt.axhline(y=mf_energy, color="tab:green", label="mean-field")
    plt.legend()
    fig.savefig("best_energies.png")
    
    fig=plt.figure()
    for i,x in enumerate(energies):
        plt.plot([i]*len(x), x, marker="o", linestyle="")
    for i,x in enumerate(random_energies):
        plt.plot([i]*len(x), x, marker=".", linestyle="")
    if exact is not None: plt.axhline(y=exact, color="tab:red", label="exact ground state")
    plt.axhline(y=mf_energy, color="tab:green", label="mean-field")
    plt.legend()
    fig.savefig("energies.png")
   
    fig=plt.figure()
    for i,x in enumerate(energies):
        plt.plot([i]*len(x), x, marker="x", linestyle="")
    for i,x in enumerate(min_max_random_energies):
        plt.plot([i]*len(x), x, marker=".", linestyle="")
    if exact is not None: plt.axhline(y=exact, color="tab:red", label="exact ground state")
    plt.axhline(y=mf_energy, color="tab:green", label="mean-field")
    plt.legend()
    fig.savefig("energies_small.png")

    fig=plt.figure()
    for i,x in enumerate(energies):
        plt.plot([i]*len(x), x, marker="x", linestyle="", color="navy")
    for i,x in enumerate(min_max_random_energies):
        plt.plot([i]*len(x), x, marker=".", linestyle="", color="tab:red")
    if exact is not None: plt.axhline(y=exact, color="tab:red", label="exact ground state")
    plt.axhline(y=mf_energy, color="tab:green", label="mean-field")
    plt.legend()
    fig.savefig("energies_small_colorcoded.png")

    fig=plt.figure()
    plt.plot(best_sample, best_vqe, marker="x", linestyle="")
    plt.xlabel("min(samples)")
    plt.ylabel("vqe")
    plt.xlim([-7.5, -2.0])
    plt.ylim([-7.5, -2.0])
    fig.savefig("samples_vs_vqe.png")


    kwargs = "".join(["{}:{}\n".format(k,v) for k,v in kwargs.items()])
        
    tex_head=r"""
    \documentclass[]{scrartcl}
    
    \usepackage[english]{babel}
    \usepackage{amsmath}
    \usepackage{amssymb}
    \usepackage{graphicx}
    \usepackage{xspace}
    \usepackage{booktabs}
    \usepackage{xcolor}
    \usepackage{tikz}
    
    
    \begin{document}
    """
    tex_tail=r"""
    \end{document}
    """
    
    tex_main=r"""
    \section*{Workflow information}
    \begin{itemize}
    \item No weights involved, all random
    \item Circuit connectiviy is restricted (if not mentioned otherwise in \texttt{kwargs} this is local-line connectivity - no pbc)
    \item Circuits are forced to be dense (as many operations in one layer as possible)
    \item First layer is always Ry on every qubit and pre-optimized (like a mean-field -- can relax later)
    \item Max depth is restricted to number of qubits
    \item Hamiltonian: Simplified Ising model
    \item Procedue: Each circuit is optimized with initial values:
    \begin{itemize}
    \item all angles 0.0
    \item all angles random but close to 0.0
    \item \texttt{n\_trials} instances of  all angles random
    \end{itemize}
    """+"""
    \item n\_qubits = {n_qubits}
    \item g = {g:2.4f}
    \item generators = {generators}
    \item kwargs = \\begin{{verbatim}} {kwargs} \\end{{verbatim}}
    """.format(n_qubits=n_qubits, generators=generators, g=g, kwargs=str(kwargs))+r"""\end{itemize}
    
    \clearpage
    \section*{Energy Distribution}
    \begin{figure}
    \includegraphics[width=0.8\textwidth]{energies.png}
    \caption{Sorted energy distribution of all circuits}
    \end{figure}
    \clearpage
    
    \section*{Best circuits}
    """
    for name, energy in names_energies:
        tex_main += """
        \\begin{{figure}}[h]
        \\includegraphics[width=0.8\\textwidth]{{{name}}}
        \\caption{{Energy={energy:+2.4f}}}
        \\end{{figure}}
        """.format(name=name, energy=energy)
    
    tex_main += r"""
    \clearpage \section*{Worst Circuits}
    """
    for name, energy in names_energies_worst:
        tex_main += """
        \\begin{{figure}}[h]
        \\includegraphics[width=0.8\\textwidth]{{{name}}}
        \\caption{{Energy={energy:+2.4f}}}
        \\end{{figure}}
        """.format(name=name, energy=energy) 
    
    outfile="result.tex" 
    tex = tex_head + tex_main + tex_tail
    with open(outfile, "w") as f:
        print(tex, file=f)

if __name__ == "__main__":
    analyze_workflow()
