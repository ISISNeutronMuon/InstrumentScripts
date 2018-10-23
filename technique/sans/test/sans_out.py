from ISISCommandInterface import MaskFile, AddRuns, AssignSample, AssignCan
from ISISCommandInterface import TransmissionSample, TransmissionCan
from ISISCommandInterface import WavRangeReduction
MaskFile('Mask.txt')
#  example in pure h2o
sample = AddRuns([88, 92, 95, 98, 101, 104, 107])
AssignSample(sample)
trans = AddRuns([87])
TransmissionSample(trans,85)
can = AddRuns([90, 93, 96, 99, 102, 105, 108])
AssignCan(can)
can_tr = AddRuns([89])
TransmissionCan(can_tr,85)
WavRangeReduction(3, 9)
#  polar bear p1 along hairs
#  Error: Missing transmission information
#  polar bear p2 along hairs
#  Error: Missing transmission information
#  polar bear p1 across hairs
sample = AddRuns([84])
AssignSample(sample)
trans = AddRuns([83])
TransmissionSample(trans,85)
can = AddRuns([80, 86])
AssignCan(can)
can_tr = AddRuns([85])
TransmissionCan(can_tr,85)
WavRangeReduction(3, 9)
#  polar bear p2 across hairs
sample = AddRuns([82])
AssignSample(sample)
trans = AddRuns([81])
TransmissionSample(trans,85)
can = AddRuns([80, 86])
AssignCan(can)
can_tr = AddRuns([85])
TransmissionCan(can_tr,85)
WavRangeReduction(3, 9)
#  example solution 23 1mm cell
#  Error: Missing transmission information
