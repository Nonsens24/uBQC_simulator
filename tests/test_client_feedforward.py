# tests/test_client_feedforward.py

import unittest
import numpy as np
from UBQCClient import UBQCClient

class MockClient(UBQCClient):
    def __init__(self):
        self.measurement_results = {}
        self.x_dependencies = {}
        self.z_dependencies = {}
        self.phi_angles = {}
        self.pattern = {}

class TestUBQCFeedforward(unittest.TestCase):
    def test_apply_dependencies(self):
        client = MockClient()

        # Test position
        pos = (0, 0)

        # Set phi for this position
        phi = np.pi / 4
        client.phi_angles[pos] = phi

        # Set known measurement outcomes
        client.measurement_results = {
            (0, 1): 1,
            (1, 0): 0,
            (1, 1): 1,
        }

        # s_X = 1 XOR 1 = 0, s_Z = 0
        client.x_dependencies[pos] = [(0, 1), (1, 1)]
        client.z_dependencies[pos] = [(1, 0)]

        expected_phi_prime = phi % (2 * np.pi)
        phi_prime = client._apply_dependencies(pos)
        self.assertAlmostEqual(phi_prime, expected_phi_prime, places=7)

        # Now set s_X = 1, s_Z = 1 → φ′ = −φ + π
        client.x_dependencies[pos] = [(0, 1)]  # s_X = 1
        client.z_dependencies[pos] = [(1, 1)]  # s_Z = 1

        expected_phi_prime = (-phi + np.pi) % (2 * np.pi)
        phi_prime = client._apply_dependencies(pos)

        self.assertAlmostEqual(phi_prime, expected_phi_prime, places=7)

if __name__ == '__main__':
    unittest.main()
