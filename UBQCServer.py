# UBQCServer.py (fully corrected & working explicitly)
import time

import numpy as np
from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit, QuantumRegister
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector, partial_trace, Operator
from qiskit.quantum_info import partial_trace, Statevector
from qiskit_aer import Aer
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector, partial_trace, DensityMatrix
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
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




def simulate_output_subcircuit(qc_full, qreg_map, output_pos_list):
    """
    Build and simulate a subcircuit containing only the qubits and gates
    causally affecting the output qubits.

    Parameters:
        qc_full: QuantumCircuit — full brickwork circuit
        qreg_map: dict[(row, col)] → Qubit
        output_pos_list: list of [(row, col)] pairs

    Returns:
        Statevector of output qubits (in same order as output_pos_list)
    """
    from collections import deque

    # Step 1: Get flat list of output indices
    output_positions = [pos for pair in output_pos_list for pos in pair]
    output_indices = [qreg_map[pos]._index for pos in output_positions]

    # Step 2: Backward slice to find causal qubits
    needed = set(output_indices)
    used_instrs = []
    for instr, qargs, cargs in reversed(qc_full.data):
        qubits_in_instr = [q._index for q in qargs]
        if any(q in needed for q in qubits_in_instr):
            used_instrs.append((instr, qargs, cargs))
            needed.update(qubits_in_instr)

    needed = sorted(needed)
    idx_map = {orig_idx: new_idx for new_idx, orig_idx in enumerate(needed)}

    # Step 3: Build new minimal subcircuit
    qreg_sub = QuantumRegister(len(needed), "sub")
    qc_sub = QuantumCircuit(qreg_sub)

    for instr, qargs, cargs in reversed(used_instrs):
        remapped_qargs = [qreg_sub[idx_map[q._index]] for q in qargs]
        qc_sub.append(instr, remapped_qargs, cargs)

    # Step 4: Simulate subcircuit
    sim = AerSimulator(method='statevector')
    qc_sub.save_statevector()
    result = sim.run(qc_sub).result()
    state = Statevector(result.get_statevector())

    # Step 5: Extract just the output qubits (remapped)
    output_sub_indices = [idx_map[idx] for idx in output_indices]
    traced = state.trace(range(len(needed)))
    reduced = traced.partial_trace([i for i in range(len(needed)) if i not in output_sub_indices])

    # Return pure state if possible
    if reduced.is_pure():
        return reduced.to_statevector()
    return reduced


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
            if cmd.name == 'N':
                qubit_pos = cmd.which_qubit
                theta_angle = cmd.angle  # client's theta was set here explicitly
                qubit_idx = self.qreg[qubit_pos]
                self.qc.ry(np.pi / 2, qubit_idx)  # Prepare |+>
                self.qc.rz(theta_angle, qubit_idx)  # Rotate Z(theta) to get |+θ>

        # Explicit entanglement
        for cmd in pattern.commands:
            if cmd.name == 'E':
                idx1 = self.qreg[cmd.which_qubits[0]]
                idx2 = self.qreg[cmd.which_qubits[1]]
                self.qc.cz(idx1, idx2)

        # Info on backends: https://qiskit.github.io/qiskit-aer/tutorials/7_matrix_product_state_method.html
        # self.backend = Aer.get_backend('qasm_simulator')
        # self.backend = AerSimulator(method='density_matrix')
        # self.backend = AerSimulator(method='stabilizer') #Clifford group efficient for MBQC
        self.backend = AerSimulator(method='matrix_product_state') # WAAAAY FAster
        # self.backend = AerSimulator(method='statevector')

    def measure_qubit(self, qubit_pos, angle):
        qubit_idx = self.qreg[qubit_pos]

        print("Measuring qubit: {}, idx: {}".format(qubit_pos, qubit_idx))

        # Temporary circuit explicitly for each interactive measurement
        # qc_temp = self.qc.copy()

        # qc_temp.rz(-angle, qubit_idx)
        # qc_temp.h(qubit_idx)
        # qc_temp.measure(qubit_idx, qubit_idx)
        self.qc.rz(-angle, qubit_idx)
        self.qc.h(qubit_idx)
        self.qc.measure(qubit_idx, qubit_idx)

        qc_run = self.qc.copy()

        row, col = qubit_pos

        # print(f"Measuring qubit {qubit_pos} with delta {angle:.2f}")

        # If not output qubits, do interactive measurement
        # if col != self.pattern.output_[0][0][1]:
        job = self.backend.run(qc_run, shots=1)
        result = job.result()
        measured_str = list(result.get_counts().keys())[0][::-1]

        return int(measured_str[qubit_idx])
        # else:
        #     from qiskit import QuantumCircuit, QuantumRegister
        #     from qiskit_aer import AerSimulator
        #     from qiskit.quantum_info import Statevector
        #
        #     # Extract output qubit positions
        #     output_pos = [pos for pair in self.pattern.output_ for pos in pair]
        #     output_indices = [self.qreg[p].__index__ for p in output_pos]
        #
        #     # Build subcircuit over only the output qubits
        #     qreg_out = QuantumRegister(len(output_indices), name="out")
        #     qc_out = QuantumCircuit(qreg_out)
        #
        #     # Map old → new qubit indices
        #     index_map = {full_idx: sub_idx for sub_idx, full_idx in enumerate(output_indices)}
        #
        #     for instr, qargs, cargs in self.qc.data:
        #         qubit_indices = [q._index for q in qargs]
        #         if all(idx in output_indices for idx in qubit_indices):
        #             new_qargs = [qreg_out[index_map[q._index]] for q in qargs]
        #             qc_out.append(instr, new_qargs, cargs)
        #
        #     # Simulate safely
        #     try:
        #         sim = AerSimulator(method='statevector')
        #         qc_out.save_statevector()
        #         result = sim.run(qc_out).result()
        #         state = result.get_statevector(qc_out)
        #
        #         from qiskit.quantum_info import Statevector
        #
        #         if isinstance(state, Statevector):
        #             return state
        #         elif isinstance(state, (list, np.ndarray)):
        #             return Statevector(state)
        #         else:
        #             raise TypeError(f"❌ UBQCServer returned invalid state: {type(state)}")
        #
        #     except Exception as e:
        #         print("Simulation error:", e)
        #         return None

# else:
        #     from qiskit_aer import AerSimulator
        #     from qiskit.quantum_info import Statevector, partial_trace
        #
        #     # Use stabilizer simulator (Clifford-only, but very efficient)
        #     sim = AerSimulator(method='stabilizer')
        #     result = sim.run(self.qc).result()
        #     state = Statevector.from_instruction(self.qc)
        #
        #     # Get output qubit positions and indices
        #     output_pos = [pos for pair in self.pattern.output_ for pos in pair]
        #     output_indices = [self.qreg[p] for p in output_pos]
        #
        #     # Partial trace out non-output qubits
        #     all_indices = list(range(self.qc.num_qubits))
        #     non_output_indices = [i for i in all_indices if i not in output_indices]
        #     reduced = partial_trace(state, non_output_indices)
        #
        #     # Return pure statevector or density matrix
        #     if reduced.is_pure():
        #         return reduced.to_statevector()
        #     else:
        #         return reduced

    # def measure_qubit(self, qubit_pos, angle):
    #     qubit_idx = self.qreg[qubit_pos]
    #
    #     # Temporary circuit explicitly for each interactive measurement
    #     qc_temp = self.qc.copy()
    #
    #     qc_temp.rz(-angle, qubit_idx)
    #     qc_temp.h(qubit_idx)
    #     qc_temp.measure(qubit_idx, qubit_idx)
    #
    #     row, col = qubit_pos
    #
    #     # print("pattern: ", self.pattern.output_)
    #     if col != self.pattern.output_[0][0][1]:    # If not output qubits
    #         # print("pos {}, op {}, in {}".format(qubit_pos, self.pattern.output_, (qubit_idx in  self.pattern.output_)))
    #         # Run single-shot clearly and explicitly`
    #         start = time.time()
    #         job = self.backend.run(qc_temp, shots=1)
    #         result = job.result()
    #         # print("Measurement time:", time.time() - start)
    #         measured_str = list(result.get_counts().keys())[0][::-1]
    #
    #         return int(measured_str[qubit_idx])
    #     else:
    #         from qiskit_aer import AerSimulator
    #         from qiskit.quantum_info import Statevector, partial_trace
    #
    #         # Extract subcircuit
    #         output_pos = self.pattern.output_
    #         qc_sub, sub_output_indices = extract_output_subcircuit(self.qc, self.qreg, output_pos)
    #
    #         # Simulate small circuit (just output qubits)
    #         # sim = AerSimulator(method='statevector')
    #         sim = AerSimulator(method='stabilizer') # Upto a thousand qubits efficiently but inly in the clifford group
    #         qc_sub.save_statevector()
    #         result = sim.run(qc_sub).result()
    #         state = Statevector(result.get_statevector())
    #
    #         # Optional: return directly if only outputs are in subcircuit
    #         return state.data  # Pure state of output qubits



