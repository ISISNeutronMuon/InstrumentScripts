"""
Perform contrast change using a HPLC Pump
"""
from math import fabs

from genie_python import genie as g

from .base import _Movement


def go_to_pressure(pressure, speed=15.0, hold=True, wait=True, dry_run=False, maxwait=1*60*60):
    """
    Move barriers in order to reach a certain surface pressure.
    Args:
        pressure: The desired surface pressure in mN/m
        speed: Barrier speed in cm/min
        hold: hold pressure after reaching target; otherwise barriers will
              not move, even if pressure changes
        wait: True wait to reach pressure; False don't wait
        dry_run: True don't do anything just print what it will do; False otherwise
        maxwait: Maximum wait time for reaching requested value in seconds. Use None to be endless. Default 1hr.
    """
    print("** NIMA trough going to pressure = {} mN/m. Barrier speed = {} cm/min **".format(pressure, speed))
    movement = _Movement(dry_run)
    movement.dry_run_warning()
    
    g.cset("Speed", 0.0) # set speed to 0 before going into run control
    
    g.cset("Nima_mode", "Pressure Control")  # 1 for PRESSURE control, 2 for AREA control
    g.cset("Control", "START")

    g.cset("Pressure", pressure)
    g.cset("Speed", speed) # start barrie movement
    g.waitfor_block("Target_reached", "NO")
    if wait:
        g.waitfor_block("Target_reached", "YES", maxwait=maxwait) # not sure what
        
    if not hold:
        g.cset("Speed", 0.0) # set speed to 0 to stop barriers moving; pressure may change
    

def go_to_area(area, speed=15.0, wait=True, dry_run=False, maxwait=1*60*60):
    """
    Move barriers in order to reach a certain area
        area: The target area in cm^2
        speed: Barrier speed in cm/min
        wait: True wait to reach target area; False don't wait
        dry_run: True don't do anything just print what it will do; False otherwise
        maxwait: Maximum wait time for reaching requested value in seconds. Use None to be endless. Default 1hr.
    """
    print("** NIMA trough going to area = {} cm^2. Barrier speed = {} cm/min **".format(area, speed))
    movement = _Movement(dry_run)
    movement.dry_run_warning()

    g.cset("Speed", 0.0)  # set speed to 0 before going into run control

    g.cset("Nima_mode", "Area Control")  # 1 for PRESSURE control, 2 for AREA control
    g.cset("Control", "START")

    g.cset("Area", area)
    g.cset("Speed", speed)  # start barrier movement
    g.waitfor_block("Target_reached", "NO")
    if wait:
        g.waitfor_block("Target_reached", "YES", maxwait=maxwait)  # not sure what

    g.cset("Speed", 0.0)  # set speed to 0 to stop barriers moving; pressure may change
