"""
Perform contrast change using a HPLC Pump
"""
from math import fabs
from .script_actions import DryRun
from .sample import SampleGenerator

try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from mocks import g

@DryRun
def contrast_change(sample, concentrations, flow=1, volume=None, seconds=None, wait=False, dry_run=False):
    """
    Perform a contrast change.
    Args:
        sample: sample object with valve position to set for the Knauer valve
        concentrations: List of concentrations from A to D, e.g. [10, 20, 30, 40]
        flow: flow rate (as per device usually mL/min)
        volume: volume to pump; if None then pump for a time instead
        seconds: number of seconds to pump; if both volume and seconds set then volume is used
        wait: True wait for completion; False don't wait
        dry_run: True don't do anything just print what it will do; False otherwise
    """
    if dry_run:
        if wait and volume:
            return volume/flow
        else:
            return 0


    else:
        print("** Contrast change for valve{} **".format(sample.valve))
        if len(concentrations) != 4:
            print("There must be 4 concentrations, you provided {}".format(len(concentrations)))
        sum_of_concentrations = sum(concentrations)
        if fabs(100 - sum_of_concentrations) > 0.01:
            print("Concentrations don't add up to 100%! {} = {}".format(concentrations, sum_of_concentrations))
        waiting = "" if wait else "NOT "

        print("Concentration: Valve {}, concentrations {}, flow {},  volume {}, time {}, and {}waiting for completion"
              .format(sample.valve, concentrations, flow, volume, seconds, waiting))


        g.cset("knauer", sample.valve)
        g.cset("Component_A", concentrations[0])
        g.cset("Component_B", concentrations[1])
        g.cset("Component_C", concentrations[2])
        g.cset("Component_D", concentrations[3])
        g.cset("hplcflow", flow)
        if volume is not None:
            g.cset("pump_for_volume", volume)
            g.cset("start_pump_for_volume", 1)
        elif seconds is not None:
            g.cset("pump_for_time", seconds)
            g.cset("start_pump_for_time", 1)
        else:
            print("Error concentration not set neither volume or time set!")
            return
        g.waitfor_block("pump_is_on", "IDLE")

        if wait:
            g.waitfor_block("pump_is_on", "OFF")

def inject(sample, liquid, flow=1.0, volume=None, wait=False):
    if isinstance(liquid, list):
        g.cset("KNAUER2",3) # set to take HPLC input from channel 3
        g.waitfor_time(1)
        contrast_change(sample.valve, liquid, flow=flow, volume=volume, wait=wait)
    elif isinstance(liquid,str) and liquid.upper() in ["SYRINGE_1", "SYRINGE_2"]:
        g.cset("KNAUER",sample.valve)
        if liquid.upper() == "SYRINGE_1":
            g.cset("KNAUER2",1)
            g.waitfor_time(1)
            g.cset("Syringe_ID",0) # syringe A or 1
        elif liquid.upper() == "SYRINGE_2":
            g.cset("KNAUER2",2)
            g.waitfor_time(1)
            g.cset("Syringe_ID",1) # syringe B or 2 
        # calculate time, set up the syringe parameters and start the injection
        inject_time = volume / flow * 60
        g.cset("Syringe_volume", volume)
        g.cset("Syringe_rate", flow)
        g.cset("Syringe_start",1)

        if wait:
            g.waitfor_time(inject_time + 2)
    else:
        print("Please specify either Syringe_1 or Syringe_2")
            #break

