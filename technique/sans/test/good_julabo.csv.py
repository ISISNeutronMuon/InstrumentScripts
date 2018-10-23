from SansScripting import *
@user_script
def good_julabo():
    do_sans("Sample1", "AT", uamps=10, thickness=1)
    do_trans("Sample2", "AT", uamps=5, thickness=1)
    do_trans("Sample2", "BT", uamps=5, thickness=1)
    do_sans("Sample2", "BT", uamps=10, thickness=1)
    do_trans("Sample3", "CT", thickness=2, frames=3000)
    do_sans("Sample3", "CT", thickness=2, frames=6000)
