from genie_python import genie as g
import matplotlib.pyplot as plt


def scan_disc(scan_from=800, scan_to=1600, scan_step=200, max_phase=20000, uamps=4):
    """
    Scan the disc chopper phase (block for chopper phase is DiscPhase and in sync is DiscInSync).
    :param scan_from: Starting point for the scan (default 800)
    :param scan_to: Ending point for the scan (default 1600)
    :param scan_step: size of the steps to take (default 200)
    :param max_phase: the maximum phase allowed, phases smaller than 0 and larger than this are wrapped around to this
                        range e.g. for a max phase 100, -10 would be 90, 110 would be 10, 100 would be 0 (default 20000)
    :param uamps: current measure (default 4)
    """

    scan_chopper("Disc", "Disc", scan_from, scan_to, scan_step, max_phase, uamps)


def scan_t0(scan_from=300, scan_to=-400, scan_step=100, max_phase=20000, uamps=4):
    """
    Scan the t0 chopper phase (block for chopper phase is T0Phase and in sync is T0InSync).
    :param scan_from: Starting point for the scan (default 300)
    :param scan_to: Ending point for the scan (default -400)
    :param scan_step: size of the steps to take (default 100)
    :param max_phase: the maximum phase allowed, phases smaller than 0 and larger than this are wrapped around to
        this range e.g. for a max phase 100, -10 would be 90, 110 would be 10, 100 would be 0 (default 20000)
    :param uamps: current measure (default 4)
    """
    scan_chopper("TS0", "T0", scan_from, scan_to, scan_step, max_phase, uamps)


def scan_chopper(disc_name, chopper_pv_name, scan_from=800, scan_to=1600, scan_step=200, max_phase=20000, uamps=4):
    """
    Scan a disc chopper phase
    :param disc_name: Name for the disc chopper
    :param chopper_pv_name: base name for the chopper blocks, expecting a block starting with this ending in
        Phase and InSync
    :param scan_from: Starting point for the scan (default 800)
    :param scan_to: Ending point for the scan (default 1600)
    :param scan_step: size of the steps to take (default 200)
    :param max_phase: the maximum phase allowed, phases smaller than 0 and larger than this are wrapped around to this
                        range e.g. for a max phase 100, -10 would be 90, 110 would be 10, 100 would be 0 (default 20000)
    :param uamps: current measure (default 4)
    """
    # create phases list
    if scan_from < scan_to:
        step = abs(scan_step)
    else:
        step = -1 * abs(scan_step)
    phases = range(scan_from, scan_to, step)
    if phases[:-1] != scan_to:
        phases.append(scan_to)
    phases = [phase % max_phase for phase in phases]
    print("Scanning chopper phases {}".format(phases))

    # create blank plot
    fig, axis = plt.subplots()
    fig.show()

    # store original phase
    chopper_phase_pv_name = "{}Phase".format(chopper_pv_name)
    chopper_in_sync_pv_name = "{}InSync".format(chopper_pv_name)
    original_phase = g.cget(chopper_phase_pv_name)["value"]

    # start scan
    g.change_number_soft_periods(len(phases))
    g.begin(paused=True)

    # for each phase change phase, wait for phase to be in sync, plot
    for period_number, phase in enumerate(phases):
        g.cset(chopper_phase_pv_name, phase)
        g.waitfor_block(chopper_in_sync_pv_name, "YES")

        g.change_period(period_number + 1)
        g.change_title("{} chopper phase scan phase= {}us".format(disc_name, phase))
        g.resume()
        g.waitfor_uamps(uamps)
        g.pause()

        spec = g.get_spectrum(period_number + 1)
        axis.plot(spec["time"], spec["signal"], marker="", label=str(phase))
        fig.legend()
        plt.show()

    g.end()
    g.cset(chopper_phase_pv_name, original_phase)
