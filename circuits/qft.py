import numpy as np
from QCompute.OpenService.service_ubqc.client.qobject import Circuit

def cp(circuit, theta, control, target):
    circuit.rz(theta / 2, control)
    circuit.rz(theta / 2, target)
    circuit.cnot([control, target])
    circuit.rz(-1 * theta / 2, target)
    circuit.cnot([control, target])

def qft_rotations(circuit, n):
    circuit.h(n)
    for qubit in range(n + 1, circuit.get_width()):
        cp(circuit, np.pi / 2 ** (qubit - n), qubit, n)

def swap_gates(circuit, one, two):
    circuit.cnot([one, two])
    circuit.cnot([two, one])
    circuit.cnot([one, two])

def swap_registers(circuit, n):
    for qubit in range(n // 2):
        swap_gates(circuit, qubit, n - qubit - 1)
    return circuit

def qft(circuit, n):
    """
    Implements a quantum fourrier transform unitary circuit on n input qubits
    :param circuit: QCompute circuit type
    :param n: number of input qubits
    :return: qft circuit
    """
    for i in range(n):
        qft_rotations(circuit, i)
    swap_registers(circuit, n)

    return circuit