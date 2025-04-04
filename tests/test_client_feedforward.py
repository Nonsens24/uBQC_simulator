# tests/test_client_feedforward.py

import unittest
import numpy as np
from UBQCClient import UBQCClient

class TestUBQCFeedforward(unittest.TestCase):
    def test_apply_dependencies(self):
        # Instantiate client with dummy layout and angles
        dummy_layout = [[0]]  # 1x1 graph
        dummy_phis = {(0, 0): np.pi / 4}
        client = UBQCClient(dummy_layout, dummy_phis)

        # Inject known measurement results
        client.measurement_results = {
            (0, 1): 1,
            (1, 0): 0,
            (1, 1): 1,
        }

        # Set dependencies for (0,0)
        client.x_dependencies = {
            (0, 0): [(0, 1), (1, 1)]  # s_X = 1 XOR 1 = 0
        }
        client.z_dependencies = {
            (0, 0): [(1, 0)]  # s_Z = 0
        }

        phi = np.pi / 4  # 45 degrees
        expected_phi_prime = ((-1)**0) * phi + 0 * np.pi  # = phi

        phi_prime = client._apply_dependencies(phi, 0, 0)

        self.assertAlmostEqual(phi_prime, expected_phi_prime % (2 * np.pi), places=7)

        # Now change dependency to make s_X = 1, s_Z = 1
        client.x_dependencies[(0, 0)] = [(0, 1)]  # s_X = 1
        client.z_dependencies[(0, 0)] = [(1, 1)]  # s_Z = 1

        expected_phi_prime = ((-1)**1) * phi + np.pi  # = -phi + π
        phi_prime = client._apply_dependencies(phi, 0, 0)

        # normalize to [0, 2π]
        expected_phi_prime = expected_phi_prime % (2 * np.pi)

        self.assertAlmostEqual(phi_prime, expected_phi_prime, places=7)

if __name__ == '__main__':
    unittest.main()
