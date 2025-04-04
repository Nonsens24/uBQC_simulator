from transpiler import transpile_to_bw_QCompute
from UBQCClient import UBQCClient
from UBQCServer import UBQCServer
from visualiser import plot_brickwork_graph_bfk_format


def main():
    circuit = example_circuit()
    pattern = transpile_to_bw_QCompute(circuit)

    client = UBQCClient(pattern)
    server = UBQCServer(pattern)

    plot_brickwork_graph_bfk_format(pattern)

    measured_qubits = [cmd.which_qubit for cmd in pattern.commands if cmd.name == 'M']

    for qubit in measured_qubits:
        delta = client.get_delta(qubit)
        measurement = server.measure_qubit(qubit, delta)
        client.receive_result(qubit, measurement)
        # print("qubit: ", qubit)

if __name__ == "__main__":
    main()

