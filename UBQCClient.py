# UBQCClient.py (exactly as you provided explicitly)
import math
import random

class UBQCClient:
    def __init__(self, pattern):
        self.pattern = pattern
        self.phi_angles = {}
        self.theta = {}
        self.r = {}
        self.s = {}
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
            self.s[pos] = result
            print(f"Client received measurement of qubit {pos}: {result}")
        else:
            print("Output state: ", result)
            self.output = result

    def _apply_dependencies(self, pos):
        for cmd in self.pattern.commands:
            if cmd.name == 'M' and cmd.which_qubit == pos:
                phi = self.phi_angles[pos]
                s_domain = sum(self.s.get(q, 0) for q in cmd.domain_s) % 2
                t_domain = sum(self.s.get(q, 0) for q in cmd.domain_t) % 2
                sign = (-1) ** s_domain
                phi_prime = (sign * phi + t_domain * math.pi) % (2 * math.pi)
                return phi_prime
        raise ValueError(f"No measurement command found for {pos}")

    def get_output_state(self):
        return self.output
