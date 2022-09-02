from genie_python import genie as g
from time import sleep
from typing import List
from threading import Thread, Event, current_thread


class StoppableThread(Thread):
    """Thread class with a stop() method."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = Event()

    def _stopped(self):
        return self._stop_event.is_set()

    def stop(self):
        self._stop_event.set()    


def restart_ioc_when_pv_in_alarm(block_to_monitor: str, iocs_to_restart: List[str], error_states: List[str],
                                 wait_between_restarts: int = 120, wait_for_polling: int = 10) -> StoppableThread:
    """
    Monitor and restart an IOC when a pv goes into a specified alarm state.
    :param block_to_monitor: Block to monitor PV status.
    :param iocs_to_restart: List of IOCs to restart if the block goes into an alarm.
    :param error_states: List of error states that should cause the IOC to restart
    :param wait_between_restarts: The time (seconds) to wait between restarts
    :param wait_for_polling: The time (seconds) to wait between polling for the block's value
    :return the thread where the restart function is running
    :rtype StoppableThread
    """
    a = StoppableThread(target=_poll_and_restart_ioc_in_alarm,
                        args=[block_to_monitor, error_states, iocs_to_restart, wait_between_restarts, wait_for_polling])
    a.setDaemon(True)
    a.start()
    return a


def _poll_and_restart_ioc_in_alarm(block_to_monitor, error_states, iocs_to_restart, wait_between_restarts, wait_for_polling):
    while not current_thread()._stopped():
        block_details = g.cget(block_to_monitor)
        if block_details["value"] in error_states:
            for ioc in iocs_to_restart:
                print("Restarting {}".format(ioc))
                g.set_pv("CS:PS:{}:RESTART".format(ioc), 1, is_local=True)
            sleep(wait_between_restarts)
        sleep(wait_for_polling)
