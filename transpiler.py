# transpiler.py
from QCompute import *
from QCompute.OpenService.service_ubqc.client.qobject import Circuit
from QCompute.OpenService.service_ubqc.client.mcalculus import MCalculus
from QCompute.OpenService.service_ubqc.client.qobject import Pattern

def transpile_to_bw_QCompute(circuit: Circuit):
    """
    Function generates optimised description of a brickwork graph as done in QCompute
    :returns brickwork pattern description
    """
    circuit.simplify_by_merging()
    circuit.to_brickwork()
    mc = MCalculus()
    mc.set_circuit(circuit)
    mc.to_brickwork_pattern() # Returns the wild (not standard) brickwork pattern
    mc.standardize()
    pattern = mc.get_pattern()

    # pattern.print_command_list()

    return pattern
