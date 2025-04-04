# UBQCServer.py (fully corrected & working explicitly)
import time
from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit, QuantumRegister
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector, partial_trace
from qiskit.quantum_info import partial_trace, Statevector
from qiskit_aer import Aer


from collections.abc import Iterable

def extract_output_subcircuit(qc_full, qreg_map, output_pos_list):
    # Flatten output position pairs to a list of (row, col)
    flat_output_pos_list = [pos for pair in output_pos_list for pos in pair]

    # Get the corresponding qubit indices
    output_indices = [qreg_map[pos] for pos in flat_output_pos_list]

    # Create a new quantum register and subcircuit
    qreg_out = QuantumRegister(len(output_indices), name="out")
    qc_out = QuantumCircuit(qreg_out)

    # Map old qubit indices → new subcircuit indices
    index_map = {full_idx: sub_idx for sub_idx, full_idx in enumerate(output_indices)}

    for instr, qargs, cargs in qc_full.data:
        involved = [q._index for q in qargs]
        # Only keep gates acting only on output qubits
        if all(idx in output_indices for idx in involved):
            new_qargs = [qreg_out[index_map[q._index]] for q in qargs]
            qc_out.append(instr, new_qargs, cargs)

    return qc_out, list(range(len(output_indices)))

class UBQCServer:
    def __init__(self, pattern):
        self.pattern = pattern

        # Explicitly store and index qubits by their positions (pattern.space)
        self.qreg = {pos: idx for idx, pos in enumerate(sorted(pattern.space))}
        total_qubits = len(self.qreg)

        # Initialize circuit explicitly with correct qubit number
        self.qc = QuantumCircuit(total_qubits, total_qubits)

        # Explicit initialization using client theta angles (set in pattern commands)
        for cmd in pattern.commands:
            if cmd.name == 'M':
                qubit_pos = cmd.which_qubit
                theta_angle = cmd.angle  # client's theta was set here explicitly
                qubit_idx = self.qreg[qubit_pos]
                self.qc.rx(theta_angle, qubit_idx)

        # Explicit entanglement
        for cmd in pattern.commands:
            if cmd.name == 'E':
                idx1 = self.qreg[cmd.which_qubits[0]]
                idx2 = self.qreg[cmd.which_qubits[1]]
                self.qc.cz(idx1, idx2)

        # Info on backends: https://qiskit.github.io/qiskit-aer/tutorials/7_matrix_product_state_method.html
        # self.backend = Aer.get_backend('qasm_simulator')
        # self.backend = AerSimulator(method='density_matrix')
        self.backend = AerSimulator(method='matrix_product_state') # WAAAAY FAster





    def measure_qubit(self, qubit_pos, angle):
        qubit_idx = self.qreg[qubit_pos]

        # Temporary circuit explicitly for each interactive measurement
        qc_temp = self.qc.copy()

        # Basis rotation clearly as per UBQC protocol
        qc_temp.ry(-2 * angle, qubit_idx)

        # Explicit measurement (exactly once) on the correct classical bit
        qc_temp.measure(qubit_idx, qubit_idx)

        row, col = qubit_pos

        # print("pattern: ", self.pattern.output_)
        if col != self.pattern.output_[0][0][1]:    # If not output qubits
            # print("pos {}, op {}, in {}".format(qubit_pos, self.pattern.output_, (qubit_idx in  self.pattern.output_)))
            # Run single-shot clearly and explicitly`
            start = time.time()
            job = self.backend.run(qc_temp, shots=1)
            result = job.result()
            print("Measurement time:", time.time() - start)
            measured_str = list(result.get_counts().keys())[0][::-1]

            return int(measured_str[qubit_idx])
        else:
            from qiskit_aer import AerSimulator
            from qiskit.quantum_info import Statevector, partial_trace

            # Extract subcircuit
            output_pos = self.pattern.output_
            qc_sub, sub_output_indices = extract_output_subcircuit(self.qc, self.qreg, output_pos)

            # Simulate small circuit (just output qubits)
            sim = AerSimulator(method='statevector')
            qc_sub.save_statevector()
            result = sim.run(qc_sub).result()
            state = Statevector(result.get_statevector())

            # Optional: return directly if only outputs are in subcircuit
            return state.data  # Pure state of output qubits

        # else:
        #     print("Calculating output qubit state vector")
        #     # Save full statevector
        #     qc_temp.save_statevector()
        #
        #     print("1")
        #     result = self.backend.run(qc_temp).result()
        #     full_state = result.get_statevector()
        #     print("2")
        #     # Identify which qubits are output (by index)
        #     # Suppose qubit_map is a dict like {(col, row): qubit_index}
        #     output_qubits = self.pattern.output_
        #     print("3")
        #     # Now trace out everything else
        #     all_qubits = list(range(qc_temp.num_qubits))
        #     print("4")
        #     non_output_qubits = list(set(all_qubits) - set(output_qubits))
        #     print("5")
        #     # Get reduced state
        #     reduced_state = partial_trace(Statevector(full_state), non_output_qubits)
        #     print("6")
        #     # Optional: convert to state vector if pure
        #     if reduced_state.is_pure():
        #         output_state = reduced_state.data[:, 0]  # first (and only) column
        #     else:
        #         output_state = reduced_state  # it's a density matrix
        #
        #     return output_state

            # qc_temp.save_statevector()
            # print("state vector saved")
            #
            # # explicitly return the full state vector for the output qubit
            # start = time.time()
            # result = self.backend.run(qc_temp).result()
            # statevector = result.get_statevector(qc_temp)
            # print(f"Statevector extraction time for output qubit {qubit_pos}: ", time.time() - start)
            #
            # return statevector


