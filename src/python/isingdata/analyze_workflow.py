import json
import tequila as tq
from .genencoder import CircuitGenEncoder
import matplotlib.pyplot as plt

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
    n_qubits = None
    kwargs = None
    generators = None
    g = None
    for k1,v1 in data.items():
        isingdata += (v1["isingdata"]["data"])
        gs_energy = v1["isingdata"]["exact_ground_state"]
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
    
    circuits = []
    for x in isingdata:
        print("energy=", x["energy"], " circuit=", x["circuit"])
        circuits += [(x["energy"], encoder(x["circuit"]), x["variables"])]
    
    circuits = sorted(circuits, key=lambda x:x[0])
    energies = [x[0] for x in circuits]
    
    names_energies=[]
    n_qubits = 0
    for i,x in enumerate(circuits):
        U = encoder.prune_circuit(x[1],variables=x[2])
        n_qubits = max(n_qubits,U.n_qubits)
        print("energy = ", x[0])
        print("variables = ", x[2])
        name = "circuit_{}.pdf".format(i)
        tq.circuit.export_to(U, filename=name)
        names_energies += [(name, x[0])]
        if i>4:
            break
    
    print("exact ground state energy", exact)
    plt.plot(energies, label="optimized circuits", color="navy")
    plt.axhline(y=exact, color="tab:red", label="exact ground state")
    plt.plot(energies)
    plt.savefig("energies.pdf")
    
    
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
    \includegraphics[width=0.8\textwidth]{energies.pdf}
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
    
    for i,x in enumerate(reversed(circuits)):
        U = encoder.prune_circuit(x[1],variables=x[2])
        energy = x[0]
        name = "worst_circuit_{}.pdf".format(i)
        encoder.export_to(U, filename=name)
        tex_main += """
        \\begin{{figure}}[h]
        \\includegraphics[width=0.8\\textwidth]{{{name}}}
        \\caption{{Energy={energy:+2.4f}}}
        \\end{{figure}}
        """.format(name=name, energy=energy)
        if i==2:
            break
    
    outfile="result.tex" 
    tex = tex_head + tex_main + tex_tail
    with open(outfile, "w") as f:
        print(tex, file=f)

if __name__ == "__main__":
    analyze_workflow()
