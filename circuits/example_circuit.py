from QCompute.OpenService.service_ubqc.client.qobject import Circuit
from qiskit import QuantumCircuit



def example_circuit():
    """
    Small example circuit to test and interpret graphs
    :return: circuit
    """
    circuit = Circuit(2)
    circuit.h(0)
    circuit.cnot([0, 1])
    # circuit.cnot([1,2])
    # circuit.cnot([2,3])
    # circuit.cnot([3,4])
    circuit.measure()

    return circuit

def example_circuit_qiskit():
    circ = QuantumCircuit(2)
    circ.h(0)
    circ.cx(0, 1)
    return circ