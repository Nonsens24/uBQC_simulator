from QCompute.OpenService.service_ubqc.client.qobject import Circuit
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace, state_fidelity, partial_trace
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

import circuits.example_circuit
import utils
from circuits.example_bw_generator import MBQCPattern, create_mbqc_pattern
from circuits.example_circuit import example_circuit
from circuits.example_circuit import example_circuit_qiskit
from transpiler import transpile_to_bw_QCompute
from UBQCClient import UBQCClient
from UBQCServer import UBQCServer
from visualiser import plot_brickwork_graph_bfk_format
from circuits.qft import qft

def manual_trace_distance(rho, sigma):
    """Compute trace distance between two DensityMatrix objects."""
    delta = rho.data - sigma.data
    s = np.linalg.svd(delta, compute_uv=False)
    return 0.5 * np.sum(s)



def compare_quantum_states(ref_state, test_state, label="UBQC"):
    """
    Compare two quantum states (pure or mixed).
    - ref_state, test_state: Statevector or DensityMatrix
    """
    from qiskit.quantum_info import Statevector, DensityMatrix, state_fidelity

    # Convert to DensityMatrix if needed
    if isinstance(ref_state, Statevector):
        ref_dm = DensityMatrix(ref_state)
    else:
        ref_dm = ref_state

    if isinstance(test_state, Statevector):
        test_dm = DensityMatrix(test_state)
    else:
        test_dm = test_state

    # Compute trace distance (always defined)
    td = manual_trace_distance(ref_dm, test_dm)
    print(f"\n‣ Trace distance between reference and {label} state: {td:.4e}, 0: identical, 1: perfectly distinguishable")

    # Compute fidelity
    if isinstance(ref_state, Statevector) and isinstance(test_state, Statevector):
        phase = np.vdot(ref_state.data, test_state.data)
        aligned = test_state.data * np.exp(-1j * np.angle(phase))
        l2 = np.linalg.norm(ref_state.data - aligned)
        print(f"‣ L2 norm of statevector difference (after global phase alignment): {l2:.2e}")
        fid = np.abs(phase) ** 2  # Fidelity between pure states
    else:

        print("ref_state:", type(ref_state))
        print("test_state:", type(test_state))

        # Double check both are valid density matrices
        if not isinstance(ref_dm, DensityMatrix) or not isinstance(test_dm, DensityMatrix):
            raise ValueError("Both reference and test states must be DensityMatrix or Statevector.")
        fid = state_fidelity(ref_dm, test_dm)

    return fid, td



def interpret_quantum_state_similarity(fidelity=None, trace_dist=None, tol=1e-3):
    """
    Print human-readable interpretation of quantum state similarity.

    Parameters:
        fidelity (float): Fidelity in [0, 1]
        trace_dist (float): Trace distance in [0, 1]
        tol (float): Tolerance for "close enough"
    """
    if fidelity is not None:
        print(f"\n🧮 Fidelity: {fidelity:.6f}")
        if abs(fidelity - 1) < tol:
            print("✅ States are indistinguishable (high fidelity)")
        elif fidelity > 0.99:
            print("✅ States are very close (within 1%)")
        elif fidelity > 0.9:
            print("⚠️ States are close, but not identical")
        else:
            print("❌ States differ significantly")

    if trace_dist is not None:
        print(f"\n🧮 Trace distance: {trace_dist:.6f}")
        if trace_dist < tol:
            print("✅ States are indistinguishable (low trace distance)")
        elif trace_dist < 0.01:
            print("✅ States are very close (within 1%)")
        elif trace_dist < 0.1:
            print("⚠️ States are somewhat distinguishable")
        else:
            print("❌ States are significantly different")

def main():

    outputs = []

    # - qubits: list of all qubit indices.
    # - input_qubits: qubits to mark as inputs.
    # - output_qubits: qubits to mark as outputs.
    # - entanglements: list of (q1, q2) entanglement operations.
    # - measurements: list of (q, angle, dependencies), where dependencies is e.g. [('s', 1)]
    # - corrections: list of (qubit, 'X'/'Z', condition), where condition is e.g. ('s', 1)

    # def create_mbqc_pattern(qubits: List[int],
    #                         input_qubits: List[int],
    #                         output_qubits: List[int],
    #                         entanglements: List[Tuple[int, int]],
    #                         measurements: List[Tuple[int, float, List[Tuple[str, int]]]],
    #                         corrections: List[Tuple[int, str, Tuple[str, int]]]) -> MBQCPattern:

    # bw_desc = create_mbqc_pattern([10], [0, 5], [4, 9], [(0, 1)],
    #                                                      [(0, 0)], [(1, 'X', ('s', 1))])

    # print(bw_desc.corrections)

    for i in range(20):

        n = 2
        circuit = example_circuit()

        pattern = transpile_to_bw_QCompute(circuit)
        # pattern.print_command_list()

        plot_brickwork_graph_bfk_format(pattern)

        client = UBQCClient(pattern)
        server = UBQCServer(pattern)

        # plot_brickwork_graph_bfk_format(pattern)

        # Create a list of all measurement commands
        pending = [cmd for cmd in pattern.commands if cmd.name == 'M']
        measured = set()  # Set to track measured qubits


        while pending:
            # Loop through pending measurements
            for cmd in pending[:]:  # Work on a snapshot to safely remove from list
                pos = cmd.which_qubit
                deps = cmd.domain_s + cmd.domain_t

                # Ensure all dependencies (domain_s + domain_t) are measured
                if all(dep in measured for dep in deps):
                    # Get delta for the qubit
                    delta = client.get_delta(pos)

                    # Perform measurement for the qubit with delta
                    measurement = server.measure_qubit(pos, delta)

                    # Receive the result and apply r flip
                    client.receive_result(pos, measurement)

                    # Mark the qubit as measured
                    measured.add(pos)

                    # Remove this command from pending list
                    pending.remove(cmd)
        outputs.append(client.get_output_vals())
        print("Out: ", client.get_output_vals())

    bitstrings = [''.join(map(str, m)) for m in outputs]

    # Count the occurrences of each bitstring
    counts = Counter(bitstrings)

    # Plot the histogram
    plt.bar(counts.keys(), counts.values(), edgecolor='black')
    plt.xlabel('Qubit state (bitstring)')
    plt.ylabel('Counts')
    plt.title('Histogram of Qubit Measurement Outcomes')
    plt.grid(True, axis='y')
    plt.show()
    print("output bits: ", client.get_output_vals())

    print("Computing Qiskit reference solution:\n")
    # qc, reference_output_state = utils.QCompute_circuit_to_qiskit_statevector(circuit)
    qc = example_circuit_qiskit()
    reference_output_state = Statevector.from_instruction(qc)


    # out = client.get_output_state()
    # print("🧪 Output state type:", type(out))

    # print("ref state: ", reference_output_state)
    # print("bw state output state: ", client.get_output_state())
    #
    # print("🧪 Output state content:", out)

    print("\n Comparing reference output to UBQC result:")
    # fid, td = compare_quantum_states(reference_output_state, client.get_output_state())


if __name__ == "__main__":
    main()


#
