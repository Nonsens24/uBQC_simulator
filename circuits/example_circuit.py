from QCompute.OpenService.service_ubqc.client.qobject import Circuit

def example_circuit():
    """
    Small example circuit to test and interpret graphs
    :return: circuit
    """
    circuit = Circuit(2)
    circuit.h(0)
    circuit.cnot([0,1])
    circuit.measure()

    return circuit