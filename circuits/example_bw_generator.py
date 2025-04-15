from typing import List, Tuple

class MBQCPattern:
    def __init__(self):
        self.qubits = set()
        self.inputs = set()
        self.outputs = set()
        self.entanglements = []
        self.measurements = []
        self.corrections = []

    def add_qubit(self, q):
        self.qubits.add(q)

    def set_inputs(self, inputs: List[int]):
        self.inputs.update(inputs)

    def set_outputs(self, outputs: List[int]):
        self.outputs.update(outputs)

    def add_entanglement(self, q1, q2):
        self.entanglements.append((q1, q2))

    def add_measurement(self, q, angle, deps=[]):
        # deps: list of (type, qubit), e.g., [('s', 1), ('s', 2)]
        self.measurements.append((q, angle, deps))

    def add_correction(self, qubit, corr_type, condition):
        # corr_type: 'X' or 'Z'; condition: (signal_type, qubit)
        self.corrections.append((qubit, corr_type, condition))

    def __str__(self):
        pattern = []
        pattern.append(f"I {' '.join(map(str, sorted(self.inputs)))}")
        pattern.append(f"O {' '.join(map(str, sorted(self.outputs)))}")
        for q1, q2 in self.entanglements:
            pattern.append(f"E {q1} {q2}")
        for q, angle, deps in self.measurements:
            dep_str = ' '.join([f"{t}{j}" for t, j in deps])
            pattern.append(f"M {q} {angle}" + (f" {dep_str}" if dep_str else ""))
        for q, ctype, (t, j) in self.corrections:
            pattern.append(f"{ctype} {q} {t}{j}")
        return "\n".join(pattern)

def create_mbqc_pattern(qubits: List[int],
                        input_qubits: List[int],
                        output_qubits: List[int],
                        entanglements: List[Tuple[int, int]],
                        measurements: List[Tuple[int, float, List[Tuple[str, int]]]],
                        corrections: List[Tuple[int, str, Tuple[str, int]]]) -> MBQCPattern:
    """
    Create an MBQC pattern.

    Parameters:
    - qubits: list of all qubit indices.
    - input_qubits: qubits to mark as inputs.
    - output_qubits: qubits to mark as outputs.
    - entanglements: list of (q1, q2) entanglement operations.
    - measurements: list of (q, angle, dependencies), where dependencies is e.g. [('s', 1)]
    - corrections: list of (qubit, 'X'/'Z', condition), where condition is e.g. ('s', 1)

    Returns:
    - MBQCPattern object (string printable).
    """
    pattern = MBQCPattern()
    for q in qubits:
        pattern.add_qubit(q)
    pattern.set_inputs(input_qubits)
    pattern.set_outputs(output_qubits)
    for e in entanglements:
        pattern.add_entanglement(*e)
    for m in measurements:
        pattern.add_measurement(*m)
    for c in corrections:
        pattern.add_correction(*c)
    return pattern
