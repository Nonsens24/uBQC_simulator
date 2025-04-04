# main.py (fully compliant with UBQC protocol)
from QCompute.OpenService.service_ubqc.client.qobject import Circuit
from QCompute import H, CX
from transpiler import transpile_to_bw_QCompute
from UBQCClient import UBQCClient
from UBQCServer import UBQCServer

def example_circuit():
    circuit = Circuit(2)
    circuit.h(0)
    circuit.cnot([0,1])
    circuit.measure()
    return circuit


def main():
    circuit = example_circuit()
    pattern = transpile_to_bw_QCompute(circuit)

    client = UBQCClient(pattern)
    server = UBQCServer(pattern)

    measured_qubits = [cmd.which_qubit for cmd in pattern.commands if cmd.name == 'M']

    for qubit in measured_qubits:
        delta = client.get_delta(qubit)
        measurement = server.measure_qubit(qubit, delta)
        client.receive_result(qubit, measurement)
        # print("qubit: ", qubit)

if __name__ == "__main__":
    main()

