"""A module to import genie_python even when genie is not available

Impoting `gen` from this module will import genie_python in the
instance where it does exist and will create a mock virtual instrument
when it does not.  You can directly import this mock instrument by
importing `mock_gen`.

"""
import mock
mock_gen = mock.Mock()
mock_gen.mock_state = "SETUP"


def begin(*_, **_kwargs):
    """Fake starting a measurement"""
    mock_gen.mock_state = "RUNNING"
    mock_gen.mock_frames = 0


def end():
    """Fake stopping a measurement"""
    mock_gen.mock_state = "SETUP"


MOTORS = {"CoarseZ": 0, "Translation": 0, "SampleX": 0,
          "SamplePos": "", "T0Phase": 0, "TargetDiskPhase": 0,
          "InstrumentDiskPhase": 0, "m4trans": 0,
          "Julabo1_SP": 0, "a1hgap": 0, "a1vgap": 0,
          "s1hgap": 0, "s1vgap": 0}


def cset_sideffect(axis=None, value=None, **kwargs):
    """Fake setting a motor"""
    if axis:
        kwargs[axis] = value
    for k in kwargs:
        if k not in MOTORS:
            raise RuntimeError("Unknown Block {}".format(k))
        MOTORS[k] = kwargs[k]


mock_gen.begin.side_effect = begin
mock_gen.end.side_effect = end
mock_gen.get_runstate.side_effect = lambda: mock_gen.mock_state
mock_gen.cset.side_effect = cset_sideffect
mock_gen.cget.side_effect = lambda axis: MOTORS[axis]

mock_gen.mock_sample_pars = {
    "GEOMETRY": "Flat Plate",
    "WIDTH": 10,
    "HEIGHT": 10,
    "THICK": 1}
mock_gen.get_sample_pars.side_effect = lambda: mock_gen.mock_sample_pars
mock_gen.get_frames = lambda: mock_gen.mock_frames
mock_gen.get_uamps = lambda: mock_gen.mock_frames/900.0


def waitfor(**kwargs):
    """Update frames in response to waiting."""
    if "frames" in kwargs:
        mock_gen.mock_frames = max(mock_gen.mock_frames, kwargs["frames"])
    elif "uamps" in kwargs:
        mock_gen.mock_frames = max(mock_gen.mock_frames, 900*kwargs["uamps"])
    elif "seconds" in kwargs:
        mock_gen.mock_frames = max(mock_gen.mock_frames, 10*kwargs["seconds"])
    elif "minutes" in kwargs:
        mock_gen.mock_frames = max(mock_gen.mock_frames, 600*kwargs["minutes"])
    elif "hours" in kwargs:
        mock_gen.mock_frames = max(mock_gen.mock_frames, 36000*kwargs["hours"])


mock_gen.waitfor.side_effect = waitfor


def change_sample_pars(key, value):
    """Fake change the sample parameters."""
    if key.upper() == "THICK":
        mock_gen.mock_sample_pars["THICK"] = value


mock_gen.change_sample_par.side_effect = change_sample_pars


def set_pv(pv_name, value):
    """Fake setting a PV value"""
    if "pwonoff" in pv_name:
        mock_gen.mock_detector_on = value


def get_pv(pv_name):
    """Fake getting a PV value"""
    if "hv0" in pv_name:
        if mock_gen.mock_detector_on == "On":
            return "On"
        return "Off"
    return mock_gen.mock_get_pv(pv_name)


mock_gen.get_pv.side_effect = get_pv
mock_gen.set_pv.side_effect = set_pv
mock_gen.mock_detector_on = "On"

try:
    import genie_python.genie as genie  # pylint: disable=unused-import
except ImportError:
    genie = mock_gen


class SwitchGenie(object):
    """A passthrough class that switches between a real and mock genie."""
    MOCKING_MODE = False

    def __init__(self):
        pass

    def __getattr__(self, name):
        if SwitchGenie.MOCKING_MODE:
            return getattr(mock_gen, name)
        return getattr(genie, name)

    def __setattr__(self, name, value):
        if SwitchGenie.MOCKING_MODE:
            return setattr(mock_gen, name, value)
        return setattr(genie, name, value)


gen = SwitchGenie()
