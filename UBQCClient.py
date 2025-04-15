# UBQCClient.py (exactly as you provided explicitly)
import math
import random
import numpy as np
from qiskit.quantum_info import Statevector, DensityMatrix
from qiskit.quantum_info import Statevector, Operator, Pauli


class UBQCClient:
    def __init__(self, pattern):
        self.pattern = pattern
        self.phi_angles = {}
        self.theta = {}
        self.r = {}
        self.s = {}
        self.t = {}
        self.output = {}

        for cmd in self.pattern.commands:
            if cmd.name == 'M':
                pos = cmd.which_qubit
                self.phi_angles[pos] = cmd.angle
                self.theta[pos] = random.choice([k * math.pi / 4 for k in range(8)])
                self.r[pos] = random.choice([0, 1])

                cmd.angle = self.theta[pos]  # Send theta explicitly to the server

    def get_delta(self, pos):
        phi_prime = self._apply_dependencies(pos)
        theta = self.theta[pos]
        r = self.r[pos]
        delta = (phi_prime + theta + math.pi * r) % (2 * math.pi)
        return delta

    def receive_result(self, pos, result):
        if isinstance(result, int):
            self.s[pos] = result ^ self.r[pos]
        elif isinstance(result, (Statevector, DensityMatrix)):
            self.output = result
        elif isinstance(result, (list, np.ndarray)):
            self.output = Statevector(result)
        else:
            raise TypeError(f"❌ Invalid type received from server: {type(result)}")

    def _apply_dependencies(self, pos):
        for cmd in self.pattern.commands:
            if cmd.name == 'M' and cmd.which_qubit == pos:
                phi = self.phi_angles[pos]
                s_domain = 0
                t_domain = 0

                for q in cmd.domain_s:
                    s_domain += self.s[q]
                s_domain %= 2
                for q in cmd.domain_t:
                    t_domain += self.s[q]
                t_domain %= 2

                sign = (-1) ** s_domain
                phi_prime = (sign * phi + t_domain * math.pi) % (2 * math.pi)

                return phi_prime

        raise ValueError(f"No measurement command found for {pos}")

    def get_output_vals(self):

        output_bits = []
        for pair in self.pattern.output_:
            for pos in pair:
                if pos not in self.s:
                    raise ValueError(f"Output qubit {pos} has not been measured yet.")
                output_bits.append(self.s[pos])
        return output_bits


    def get_output_state(self, reference_state=None, verbose=True):
        from qiskit.quantum_info import Statevector, Operator, Pauli, state_fidelity
        import numpy as np

        def apply_pauli(corr_state, pauli_str):


            if not isinstance(corr_state, Statevector):
                corr_state = Statevector(corr_state)

            pauli_matrix = Pauli(pauli_str).to_matrix()
            corrected_state = pauli_matrix @ corr_state.data
            corrected_state = Statevector(corrected_state)


            print("########### RETURN TYPE: ", type(corrected_state))
            return corrected_state

        # Flatten output positions
        flat_output_pos = [pos for pair in self.pattern.output_ for pos in pair]
        num_outputs = len(flat_output_pos)

        # Make sure self.output is valid
        corrected_state = self.output
        print("Client out: ", corrected_state)


        if corrected_state is None:
            raise ValueError("❌ UBQCClient.output is None — was it set correctly?")
        if isinstance(corrected_state, Operator):
            raise TypeError("❌ corrected_state is an Operator — likely Pauli created but not applied.")
        if not isinstance(corrected_state, Statevector):
            corrected_state = Statevector(corrected_state)

        if verbose:
            print("Applying Pauli corrections to output state...")

        for idx, pos in enumerate(flat_output_pos):
            cmd = next((c for c in self.pattern.commands if c.name == 'M' and c.which_qubit == pos), None)
            if cmd is None:
                raise ValueError(f"No measurement command found for output qubit {pos}")

            sX = sum(self.s[q] for q in cmd.domain_s) % 2
            sZ = sum(self.s[q] for q in cmd.domain_t) % 2

            if verbose:
                print(f"Output qubit {pos} (index {idx}): sX = {sX}, sZ = {sZ}")

            if sZ:
                pauli_str = ''.join('Z' if i == idx else 'I' for i in range(num_outputs))
                corrected_state = apply_pauli(corrected_state, pauli_str)
            if sX:
                pauli_str = ''.join('X' if i == idx else 'I' for i in range(num_outputs))
                corrected_state = apply_pauli(corrected_state, pauli_str)

        if reference_state is not None:
            try:
                fid = state_fidelity(corrected_state, reference_state)
                if verbose:
                    print(f"‣ Fidelity with reference: {fid:.6f}")
            except Exception as e:
                print(f"⚠️ Could not compute fidelity: {e}")

        return corrected_state

