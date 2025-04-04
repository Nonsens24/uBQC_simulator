from QCompute.OpenService.service_ubqc.client.qobject import Circuit
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace, state_fidelity, partial_trace
import numpy as np
import utils
from circuits.example_circuit import example_circuit
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

    # If both pure → use fidelity or statevector comparison
    if isinstance(ref_state, Statevector) and isinstance(test_state, Statevector):
        phase = np.vdot(ref_state.data, test_state.data)
        aligned = test_state.data * np.exp(-1j * np.angle(phase))
        l2 = np.linalg.norm(ref_state.data - aligned)
        print(f"‣ L2 norm of statevector difference (after global phase alignment): {l2:.2e}")
    else:
        # Mixed states → use fidelity if needed
        fid = state_fidelity(ref_dm, test_dm)
        print(f"‣ Fidelity: {fid:.6f}, 0: identical, 1: orthogonal")

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

    n = 2
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

    print("Computing Qiskit reference solution:\n")
    qc, reference_output_state = utils.QCompute_circuit_to_qiskit_statevector(circuit)

    print("\n Comparing reference output to UBQC result:")
    fid, td = compare_quantum_states(reference_output_state, client.get_output_state())

    interpret_quantum_state_similarity(fid, td)

if __name__ == "__main__":
    main()



