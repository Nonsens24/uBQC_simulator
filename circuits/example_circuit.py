from QCompute.OpenService.service_ubqc.client.qobject import Circuit

def example_circuit():
    """
    Small example circuit to test and interpret graphs
    :return: circuit
    """
    circuit = Circuit(2)
    circuit.h(0)
    circuit.cnot([0,1])
    # circuit.cnot([1,2])
    # circuit.cnot([2,3])
    # circuit.cnot([3,4])
    circuit.measure()

    return circuit