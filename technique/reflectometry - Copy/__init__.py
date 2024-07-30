
# from .base import run_angle, transmission, slit_check, auto_height
from .base_New import transmission_new, run_angle_new, run_angle_SM_new, transmission_new_SM
from .base_New_v2 import transmission_new_edit, run_angle_new_edit, run_angle_SM_new_edit,\
                         transmission_new_SM_edit, slit_check, auto_height
from .contrast_change import contrast_change, inject, auto_HPLC
from .NIMA_control import go_to_pressure, go_to_area
from .sample import SampleGenerator, Sample
