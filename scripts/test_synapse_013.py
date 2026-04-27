#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["jax", "jaxlib", "jaxley"]
# ///
import jaxley as jx
from jaxley.synapses import IonotropicSynapse

print("--- Testing Jaxley 0.13.0 API ---")
class BasicCell(jx.Cell):
    def __init__(self):
        super().__init__()
        self.soma = jx.Compartment()

def probe():
    cell1 = BasicCell()
    cell2 = BasicCell()
    net = jx.Network([cell1, cell2])
    print("Methods available on net:")
    methods = [m for m in dir(net) if not m.startswith('_')]
    print(", ".join(methods))
    
    # Let's try some common connecting topologies
    print("\n[Topology Test]")
    try:
        j1 = jx.connect(cell1.soma, cell2.soma, IonotropicSynapse())
        print("1. jx.connect(comp, comp, syn) -> SUCCESS")
    except Exception as e:
        print(f"1. jx.connect -> FAIL: {e}")
    
    try:
        # In newer jaxley, it might be that make_synapse is directly inside the connect module or simply net.connect
        if hasattr(jx, 'connect'):
            print("jx.connect exists.")
    except Exception as e:
        pass

probe()
