"""
Perform contrast change using a HPLC Pump
"""
from math import fabs

from genie_python import genie as g

from .base_New_v2 import _Movement, _calculate_target_auto_height


def contrast_change(sample, concentrations, flow, volume=None, seconds=None, wait=False, dry_run=False):
    """
    Perform a contrast change.
    Args:
        sample: sample object
        concentrations: List of concentrations from A to D, e.g. [10, 20, 30, 40] if only A-C specified, D will be calculated.
        flow: flow rate (as per device usually mL/min)
        volume: volume to pump; if None then pump for a time instead
        seconds: number of seconds to pump; if both volume and seconds set then volume is used
        wait: True wait for completion; False don't wait
        dry_run: True don't do anything just print what it will do; False otherwise
    """
    print("** Contrast change for valve{} **".format(sample.valve))
    movement = _Movement(dry_run)
    movement.dry_run_warning()
    if len(concentrations) != 4 and len(concentrations) != 3:
        print("There must be 3 or 4 concentrations, you provided {}".format(len(concentrations)))
    if len(concentrations) == 3:
        print("Only 3 concentrations provided, if using a Knauer pump a 4th concentration must be provided.")
    sum_of_concentrations = sum(concentrations)
    if fabs(100 - sum_of_concentrations) > 0.01 and len(concentrations) != 3:
        print("Concentrations don't add up to 100%! {} = {}".format(concentrations, sum_of_concentrations))
    waiting = "" if wait else "NOT "

    print("Concentration: Valve {}, concentrations {}, flow {},  volume {}, time {}, and {}waiting for completion"
          .format(sample.valve, concentrations, flow, volume, seconds, waiting))

    if not dry_run:
        g.cset("knauer", sample.valve)
        g.cset("Component_A", concentrations[0])
        g.cset("Component_B", concentrations[1])
        g.cset("Component_C", concentrations[2])
        if len(concentrations) == 4:
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
        g.waitfor_block("Pump_is_on", "IDLE")
        #g.waitfor_block("Pump_is_on", "Pumping")

        if wait:
            g.waitfor_block("Pump_is_on", "OFF")
            #g.waitfor_block("Pump_is_on", "Off")

def inject(sample, liquid, flow=1.0, volume=None, wait=False):
    if isinstance(liquid, list):
        g.cset("KNAUER2",3) # set to take HPLC input from channel 3
        g.waitfor_time(1)
        contrast_change(sample, liquid, flow=flow, volume=volume, wait=wait)
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


def auto_HPLC(samp, subphase=[100, 0, 0, 0]):
    fine_height_block = "HEIGHT"
    laser_offset_block = "KEYENCE"
    target = 0.0
    try:
        keyence_status = g.cget('KEYENCE')['alarm']
        if keyence_status == 'NO_ALARM':
            target_height, current_height = _calculate_target_auto_height(laser_offset_block, fine_height_block, target)
            while target_height > current_height:
                contrast_change(samp, subphase, flow=2.0, volume=2.0, wait=True)
                g.waitfor_time(seconds=2)
                target_height, current_height = _calculate_target_auto_height(laser_offset_block, fine_height_block,
                                                                                  target)
        else:
            print('KEYENCE is in alarm state and height will not be changed.')
    except TypeError as e:
        pass
        # prompt_user = not (continue_if_nan or dry_run)
        # general.utilities.io.alert_on_error("ERROR: cannot set auto height (invalid block value): {}".format(e),
                                            # prompt_user)