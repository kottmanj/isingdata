import tequila as tq
import numpy


def simplified_ising(n_qubits, g, connectivity: dict = None):
    if connectivity is None:
        # local with periodic boundary conditions
        #connectivity = {k: [(k + 1) % n_qubits, (k - 1) % n_qubits] for k in range(n_qubits)}
        connectivity = {**{k: [k+1] for k in range(n_qubits-1)},n_qubits-1:[]}


    H = tq.paulis.Zero()
    for k, v in connectivity.items():
        H += g * tq.paulis.X(k)
        for vv in v:
            H += tq.paulis.Z([k, vv])
    return H

def manual_ansatz(n_qubits, n_layers=1, connectivity=None, static=False):
    # no pbc
    U = tq.QCircuit()
    for l in range(n_layers):
        for q in range(n_qubits):
            angle = (l,q,0) if not static else (l,0)
            angle = tq.assign_variable(angle)
            U += tq.gates.Ry(angle=angle*numpy.pi, target=q)
        for q in range(n_qubits//2):
            angle = (l, 2*q,2*q+1, 1) if not static else 1.0
            angle = tq.assign_variable(angle)
            U += tq.gates.ExpPauli(paulistring="X({})Y({})".format(2*q,2*q+1), angle=angle*numpy.pi)
            #U += tq.gates.ExpPauli(paulistring="Y({})X({})".format(2*q,2*q+1), angle=angle*numpy.pi)

        # for q in range(n_qubits):
        #     angle = (l, q,1) if not static else (l,1)
        #     U += tq.gates.Ry(angle=angle, target=q)
        for q in range(n_qubits//2-1):
            angle = (l, 2*q+1, 2*q+2, 1) if not static else 1.0
            angle = tq.assign_variable(angle)
            U += tq.gates.ExpPauli(paulistring="X({})Y({})".format(2*q+1,(2*q+2)%n_qubits), angle=angle*numpy.pi)
            #U += tq.gates.ExpPauli(paulistring="Y({})X({})".format(2*q+1,(2*q+2)%n_qubits), angle=angle*numpy.pi)

    return U


if __name__ == "__main__":

    for g in [0.1, 0.2, 0.3, 0.4, 0.5, 1.0]:
        H4 = simplified_ising(4, g=g)
        v, vv = numpy.linalg.eigh(H4.to_matrix())
        print(g, " ", tq.QubitWaveFunction(vv[:, 0]))
