from math import fabs

from genie_python import genie as g

from technique.reflectometry.base import _Movement


def contrast_change(valve_position, concentrations, flow, volume=None, seconds=None, wait=False, dry_run=False):
    """
    Perform a contrast change.
    Args:
        valve_position: valve position to set for the Knaur valve
        concentrations: List of concentrations from A to D, e.g. [10, 20, 30, 40]
        flow: flow rate (as per device usually mL/min)
        volume: volume to pump; if None then pump for a time instead
        seconds: number of seconds to pump; if noth volume and seconds set then volume is used
        wait: True wait for completion; False don't wait
        dry_run: True don't do anything just print what it will do; False otherwise
    """
    print("** Contrast change for valve{} **".format(valve_position))
    movement = _Movement(dry_run)
    movement._dry_run_warning()
    if len(concentrations) != 4:
        print("There must be 4 concentrations, you provided {}".format(len(concentrations)))
    sum_of_concentrations = sum(concentrations)
    if fabs(100 - sum_of_concentrations) > 0.01:
        print("Concentrations don't add up to 100%! {} = {}".format(concentrations, sum_of_concentrations))
    waiting = "" if wait else "NOT "

    print("Concentration: Valve {}, concentrations {}, flow {},  volume {}, time {}, and {}waiting for completion"
          .format(valve_position, concentrations, flow, volume, seconds, waiting))

    if not dry_run:
        g.cset("knauer", valve_position)
        g.cset("Component_A", concentrations[0])
        g.cset("Component_B", concentrations[1])
        g.cset("Component_C", concentrations[2])
        g.cset("Component_D", concentrations[3])
        g.cset("hplcflow", flow)
        if volume is not None:
            g.cset("pump_for_volume", volume)
        elif seconds is not None:
            g.cset("pump_for_time", seconds)
        else:
            print("Error concentration not set neither volume or time set!")
            return
        g.cset("start_timed", 1)
        g.waitfor_block("pump_is_on", "RUNNING")
        if wait:
            g.waitfor_block("pump_is_on", "STOPPED")