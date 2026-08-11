"""This module holds small utilities for the Larmor beam line

While this servers as a general placehoold for minor scripts,
An attempt should be made to keep this module small and
eventually migrate code from here into more specific modules.
"""


from logging import debug
# import time
from technique.sans.genie import gen

def flipper_on():
    gen.set_pv("IN:ZOOM:KEPCO_01:OUTPUTMODE:SP","Current")
    gen.set_pv("IN:ZOOM:KEPCO_01:VOLTAGE:SP",20)
    gen.set_pv("IN:ZOOM:KEPCO_01:CURRENT:SP",2)
    gen.set_pv("IN:ZOOM:KEPCO_01:OUTPUTSTATUS:SP","ON")
    
    gen.set_pv("IN:ZOOM:KEPCO_02:OUTPUTMODE:SP","Current")
    gen.set_pv("IN:ZOOM:KEPCO_02:VOLTAGE:SP",20)
    gen.set_pv("IN:ZOOM:KEPCO_02:CURRENT:SP",2)
    gen.set_pv("IN:ZOOM:KEPCO_02:OUTPUTSTATUS:SP","ON")   

def flipper_off():
    gen.set_pv("IN:ZOOM:KEPCO_01:OUTPUTSTATUS:SP","OFF")
    gen.set_pv("IN:ZOOM:KEPCO_02:OUTPUTSTATUS:SP","OFF")       

def flipper1(state=None):
    """Set the state of the spinflipper. """
    """Spin flipper current switches between -2 and +2. Flipper +2V is Flipper On/Active."""
    work_curr=2   
    if state==0 or state ==1:
        gen.cset('Spin_Flipper', 2*(state-0.5)*work_curr)
        
def sample_changer_position():
    #ccordinates for pos HT
    gen.cset('SampleStack_X',0) 
    gen.cset('SampleStack_Y',272.1)     
    gen.cset('SampleStack_lowZ',-25) 
    
def HTS_position():
    #ccordinates for HTS 
    gen.cset('SampleStack_X',20) 
    gen.cset('SampleStack_Y',0)     
    gen.cset('SampleStack_lowZ',147) 
    
def reset_sample_stack_limits():
    #X/Sample Changer Motion
    gen.set_pv("IN:ZOOM:MOT:MTR0401.HLM",30.5)
    gen.set_pv("IN:ZOOM:MOT:MTR0401.LLM",-30.5)
    #Y/Sample Changer Motion
    gen.set_pv("IN:ZOOM:MOT:MTR0402.HLM",300)
    gen.set_pv("IN:ZOOM:MOT:MTR0402.LLM",-300)
    #Upper Arc Motion
    gen.set_pv("IN:ZOOM:MOT:MTR0404.HLM",5)
    gen.set_pv("IN:ZOOM:MOT:MTR0404.LLM",-5)
    #Lower Arc Motion
    gen.set_pv("IN:ZOOM:MOT:MTR0405.HLM",5)
    gen.set_pv("IN:ZOOM:MOT:MTR0405.LLM",-5)
    #Rotation Motion
    gen.set_pv("IN:ZOOM:MOT:MTR0406.HLM",1.6)
    gen.set_pv("IN:ZOOM:MOT:MTR0406.LLM",-1.5)
    #Large Z
    gen.set_pv("IN:ZOOM:MOT:MTR0407.HLM",250)
    gen.set_pv("IN:ZOOM:MOT:MTR0407.LLM",-50)    
    
        





