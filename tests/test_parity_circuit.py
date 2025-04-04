import unittest
import numpy as np
from qiskit import QuantumCircuit

import transpiler
from UBQCClient import UBQCClient
from UBQCServer import UBQCServer

def build_parity_circuit(x0, x1):
    qc = QuantumCircuit(2, 1)
    if x0:
        qc.x(0)
    if x1:
        qc.x(1)
    qc.cx(0, 1)
    qc.measure(1, 0)
    return qc

class TestParityUBQC(unittest.TestCase):

    def run_parity_case(self, x0, x1):
        # Build the circuit and transpile
        qc = build_parity_circuit(x0, x1)
        layout, x_deps, z_deps = transpiler.transpile_to_bw_QCompute(qc)
        client = UBQCClient((layout, x_deps, z_deps))
        server = UBQCServer(layout)

        # Qubit preparation
        for pos, qubit in client.send_qubits():
            server.receive_qubit(pos, qubit)

        # Entanglement
        server.apply_entanglement()

        # Measurement interaction
        for pos in client.iterate_measurements():
            delta = client.send_delta(pos)
            result = server.measure_qubit(pos, delta)
            client.receive_result(pos, result)

        # Extract output from the last measured qubit on wire 1
        output_pos = max([pos for pos in client.measurement_results if pos[1] == 1], key=lambda pos: pos[0])
        ubqc_output = client.measurement_results[output_pos]
        expected = x0 ^ x1

        self.assertEqual(ubqc_output, expected,
                         f"UBQC XOR({x0}, {x1}) = {ubqc_output}, expected {expected}")

    def test_parity_00(self):
        self.run_parity_case(0, 0)

    def test_parity_01(self):
        self.run_parity_case(0, 1)

    def test_parity_10(self):
        self.run_parity_case(1, 0)

    def test_parity_11(self):
        self.run_parity_case(1, 1)

if __name__ == "__main__":
    unittest.main()
