"""This module automates the creation of reduction scripts from the run log."""

from __future__ import print_function
from xml.etree import ElementTree as ET
from collections import defaultdict

SCHEMA = "{http://definition.nexusformat.org/schema/3.0}"


def get_kind(run):
    """What type of measuremented was performed?"""
    return run.find("./{}measurement_type".format(SCHEMA)).text


def is_blank_transmission(run):
    """Was the measurement in transmission mode and on a blank?"""
    return get_kind(run) == "blank_transmission"


def is_sample(run):
    """Was the measurement in sesans mode and on a sample?"""
    kind = get_kind(run)
    return kind == "sesans" or kind == "sans"


def is_transmission(run):
    """Was the measurement in transmission mode and on a sample?"""
    return get_kind(run) == "transmission"


def is_blank(run):
    """Was the measurement in sesans mode and on a blank?"""
    return get_kind(run) == "blank"


def get_sample(run):
    """Get the name of the actual sample"""
    return run.find("./{}measurement_label".format(SCHEMA)).text


def get_sel(run):
    """Get the spin echo constant"""
    return run.find("./{}measurement_id".format(SCHEMA)).text.split(",")[1]


def get_echo_id(run):
    """Get the spin echo tune id"""
    return run.find("./{}measurement_id".format(SCHEMA)).text.split(",")[0]


def get_run_number(run):
    """Get the run number for the measurement"""
    return int(run.attrib["name"][len("LARMOR"):])


def connect_samples(runs, test):
    """Group runs with the same sample

    Parameters
    ==========
    run : list
      A list of XML nodes for the run numbers to investigate
    test : function
      A boolean to check if the run should be included

    Returns
    =======
    A dictionary of runs with their samples as the key.
    """
    result = defaultdict(list)
    for run in runs:
        if not test(run):
            continue
        sample = get_sample(run)
        result[sample].append(run)
    return result


def sans_connection(start, end, path):
    """Connect the runs for a series of sesans measurements"""
    root = ET.parse(path)
    runs = root.findall("./{}NXentry".format(SCHEMA))
    runs = [run for run in runs
            if start <= get_run_number(run) < end]

    # Identify Transmissions
    bts = connect_samples(runs, is_blank_transmission)

    # Identify Sample Names
    samples = set([get_sample(run) for run in runs if is_sample(run)])

    # Identify Sample Transmissions
    trans = {}
    for sample in samples:
        relevant = [run for run in runs if
                    get_sample(run) == sample
                    and is_transmission(run)]
        if not relevant:
            continue
        trans[sample] = relevant

    # Identify spin echo runs
    sample_runs = defaultdict(dict)
    for sample in samples:
        relevant = [run for run in runs if
                    get_sample(run) == sample
                    and is_sample(run)]
        sample_runs[sample] = relevant

    # Identify Blank Runs
    blank_parts = connect_samples(runs, is_blank)
    blank_parts = {
        key: set([get_echo_id(run) for run in blank_parts[key]])
        for key in blank_parts}

    sample_blank_pairs = set()
    for sample in sample_runs:
        for blank in blank_parts:
            sample_blank_pairs.add((sample, blank))

    final_dict = defaultdict(lambda: defaultdict(dict))
    for sample, blank in sample_blank_pairs:
        total = {}
        total["Sample"] = [get_run_number(p)
                           for p in sample_runs[sample]]
        if sample in trans and blank in bts:
            total["P0Trans"] = [get_run_number(x) for x in bts[blank]]
            total["Trans"] = [get_run_number(x)
                              for x in trans[sample]]
        echos = [get_echo_id(p) for p in sample_runs[sample]]
        total["P0"] = [get_run_number(run) for run in runs
                       if get_echo_id(run) in echos
                       and get_sample(run) == blank]
        final_dict[sample][blank] = total
    return final_dict


def sesans_connection(start, end, path):
    """Connect the runs for a series of sesans measurements"""
    root = ET.parse(path)
    runs = root.findall("./{}NXentry".format(SCHEMA))
    runs = [run for run in runs
            if start <= get_run_number(run) < end]

    # Identify Transmissions
    bts = connect_samples(runs, is_blank_transmission)

    # Identify Sample Names
    samples = set([get_sample(run) for run in runs if is_sample(run)])

    # Identify Sample Transmissions
    trans = {}
    for sample in samples:
        relevant = [run for run in runs if
                    get_sample(run) == sample
                    and is_transmission(run)]
        if not relevant:
            continue
        trans[sample] = relevant

    # Identify spin echo runs
    sample_runs = defaultdict(dict)
    for sample in samples:
        relevant = [run for run in runs if
                    get_sample(run) == sample
                    and is_sample(run)]
        sels = set([get_sel(run) for run in relevant])
        for sel in sels:
            sample_runs[sample][sel] = [run for run in relevant
                                        if get_sel(run) == sel]

    # Identify Blank Runs
    blank_parts = connect_samples(runs, is_blank)
    blank_parts = {
        key: set([get_echo_id(run) for run in blank_parts[key]])
        for key in blank_parts}

    sample_blank_pairs = set()
    for sample in sample_runs:
        echos = set()
        for sel in sample_runs[sample]:
            echos = echos.union(set([get_echo_id(x)
                                     for x in sample_runs[sample][sel]]))
        for blank in blank_parts:
            if echos.issubset(blank_parts[blank]):
                sample_blank_pairs.add((sample, blank))

    final_dict = defaultdict(lambda: defaultdict(dict))
    for sample, blank in sample_blank_pairs:
        total = {}
        for sel in sample_runs[sample]:
            total[sel] = {}
            total[sel]["Sample"] = [get_run_number(p)
                                    for p in sample_runs[sample][sel]]
            if sample in trans and blank in bts:
                total[sel]["P0Trans"] = [get_run_number(x) for x in bts[blank]]
                total[sel]["Trans"] = [get_run_number(x)
                                       for x in trans[sample]]
            echos = [get_echo_id(p) for p in sample_runs[sample][sel]]
            total[sel]["P0"] = [get_run_number(run) for run in runs
                                if get_echo_id(run) in echos
                                and get_sample(run) == blank]
        final_dict[sample][blank] = total
    return final_dict


def sesans_reduction(outfile, data, pairs):
    """Create a reduction script for sesans data

    Parameters
    ==========
    outfile : str
      The path where the script should be saved
    data : dict
      The sample dictionary extracted from the sample log
    pairs : dict
      A dictionary with sample names as the keys and the corresponding
      blank samples as the values
    """
    with open(outfile, "w") as out:
        for sample in pairs:
            for sel in data[sample][pairs[sample]]:
                out.write("reduction({})\n".format(
                    data[sample][pairs[sample]][sel]))


def sans_reduction(outfile, data, pairs, mask, direct):
    """Create a reduction script for sans data

    Parameters
    ==========
    outfile : str
      The path where the script should be saved
    data : dict
      The sample dictionary extracted from the sample log
    pairs : dict
      A dictionary with sample names as the keys and the corresponding
      blank samples as the values
    mask : str
      The mask file for the reduction
    direct : int
      The run number for the direct run
    """
    with open(outfile, "w") as out:
        out.write("from ISISCommandInterface import MaskFile, AddRuns,"
                  " AssignSample, AssignCan\n")
        out.write("from ISISCommandInterface import TransmissionSample,"
                  " TransmissionCan\n")
        out.write("from ISISCommandInterface import WavRangeReduction\n")
        out.write("MaskFile('{}')\n".format(mask))
        for sample in pairs:
            out.write("#  {}\n".format(sample))
            runinfo = data[sample][pairs[sample]]
            if "Trans" not in runinfo:
                out.write("#  Error: Missing transmission information\n")
                continue
            out.write("sample = AddRuns([{}])\nAssignSample(sample)\n".format(
                ", ".join([str(run) for run in runinfo["Sample"]])))
            out.write(
                "trans = AddRuns([{}])\nTransmissionSample(trans,{})\n".format(
                    ", ".join([str(run) for run in runinfo["Trans"]]),
                    direct))
            out.write("can = AddRuns([{}])\nAssignCan(can)\n".format(
                ", ".join([str(run) for run in runinfo["P0"]])))
            out.write(
                "can_tr = AddRuns([{}])\nTransmissionCan(can_tr,{})\n".format(
                    ", ".join([str(run) for run in runinfo["P0Trans"]]),
                    direct))
            out.write("WavRangeReduction(3, 9)\n")


def console_oracle(sample, blanks):  # pragma: no cover
    """Have the use identify the blank for a sample

    The list of possible blanks will be enumerated and displayed to
    the user.  The user can then pick an iterm off the list from the
    keyboard.

    Parameters
    ==========
    sample : str
      The name of the sample being queries
    blanks : list
      A list of possible blank samples

    """
    result = -1
    while True:
        for idx, blank in enumerate(blanks):
            print("{}: \t {}".format(idx + 1, blank))
        result = raw_input(
            "What is the blank for the sample: {}".format(sample))
        result = int(result) - 1
        if 0 <= result <= len(blanks):
            break
        print("Index {} out of range.".format(result))
    return blanks[result]


def identify_pairs(data, oracle=console_oracle):
    """Find the exact blanks for a set of sample runs

    Parameters
    ==========
    data : dict
      The dictionary of possible sample/blank setups extracted from
      the log file.
    oracle : function
      A function that takes a sample name and a list of possible
      blanks and returns the name of the correct blank.  The default
      value will print the blanks to the console and as the user to
      chose the correct blank.

    """
    result = {}
    for sample in sorted(data):
        result[sample] = oracle(sample, sorted(data[sample].keys()))
    return result
