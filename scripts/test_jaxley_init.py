#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["jaxley"]
# ///
import jaxley as jx
def test():
    try:
        class C(jx.Cell):
            def __init__(self):
                super().__init__()
                self.soma = jx.Compartment()
        cell = C()
        net = jx.Network([cell, cell])
        print("Success A")
    except Exception as e:
        print(f"Fail A: {e}")
        
    try:
        comp = jx.Compartment()
        branch = jx.Branch(comp, 1)
        cell = jx.Cell(branch)
        net = jx.Network([cell, cell])
        print("Success B")
    except Exception as e:
        print(f"Fail B: {e}")

    try:
        branch = jx.Branch(1)
        cell = jx.Cell([branch])
        net = jx.Network([cell, cell])
        print("Success C")
    except Exception as e:
        print(f"Fail C: {e}")

test()
