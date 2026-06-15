import jaxley as jx
from jaxley.channels import HH

def test_jaxley():
    # 1. Build
    cell = jx.Cell([jx.Branch(ncomp=1)], parents=[-1])
    cell.insert(HH())
    
    # 2. Record
    cell.record("v")
    
    # 3. Stimulate
    # Jaxley 0.13.0 step_current
    current = jx.step_current(i_delay=2.0, i_dur=6.0, i_amp=0.1, delta_t=0.1, t_max=10.0)
    # Applying stimulus
    cell.branch(0).comp(0).stimulate(current)
    
    # 4. Integrate
    v = jx.integrate(cell, t_max=10.0, delta_t=0.1)
    print(f"Voltage trace shape: {v.shape}")
    print(f"First 5 values: {v[0, :5]}")

if __name__ == "__main__":
    test_jaxley()
