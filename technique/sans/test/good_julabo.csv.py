from SansScripting import *
@user_script
def good_julabo():
    do_sans("Sample1", "AT", thickness=1, uamps=10)
    do_trans("Sample2", "AT", thickness=1, uamps=5)
    do_trans("Sample2", "BT", thickness=1, uamps=5)
    do_sans("Sample2", "BT", thickness=1, uamps=10)
    do_trans("Sample3", "CT", frames=3000, thickness=2)
    do_sans("Sample3", "CT", frames=6000, thickness=2)
