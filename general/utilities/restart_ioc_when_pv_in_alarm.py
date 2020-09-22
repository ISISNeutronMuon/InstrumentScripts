import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.environ["KIT_ROOT"], "ISIS", "inst_servers", "master")))

from genie_python import genie as g
from time import sleep
from server_common.helpers import register_ioc_start

IOC_TO_RUN_IN = "BGRSCRPT_02"
BLOCK_TO_MONITOR = "field_ZF_status"
IOC_TO_RESTART = ["ZFMAGFLD_01"]

WAIT_BETWEEN_RESTARTS = 120
WAIT_FOR_POLLING = 10

register_ioc_start(IOC_TO_RUN_IN)

g.set_instrument(None)

while True:
    block_details = g.cget(BLOCK_TO_MONITOR)
    block_details_second_check = g.cget(BLOCK_TO_MONITOR)
    # Check twice to make sure error is consistent
    if all([pv_update["value"] in ["No new magnetometer data", "Magnetometer data invalid"]
            for pv_update in [block_details, block_details_second_check]]):
        for ioc in IOC_TO_RESTART:
            print("Restarting {}".format(ioc))
            g.set_pv("CS:PS:{}:RESTART".format(ioc), 1, is_local=True)
        sleep(WAIT_BETWEEN_RESTARTS)
    sleep(WAIT_FOR_POLLING)
