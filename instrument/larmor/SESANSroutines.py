#file under C:\Instrument\Settings\config\NDXLARMOR\Python\LSS

import time as time
from genie_python.genie import *
from .util import flipper1
import numpy as np
import math
from matplotlib.pyplot import errorbar, plot, show
import matplotlib.pyplot as mpl
import genie_python.genie as gen
from time import sleep
from instrument.larmor.sans import setup_dae_scanningAlanis
from instrument.larmor.sans import setup_dae_scanning12
from instrument.larmor.sans import setup_dae_event
from instrument.larmor.sans import setup_dae_transmission
#from general.scans.fit import DampedOscillator
#import instrument.larmor.scans as ls

def measure_at(title, position, u=500, d=500, tot=3000, trans=False):
    if type(position) is str:
        cset(SamplePos=position)
    elif type(position) is int:
        new_set_pos(position)
    waitfor_move()
    change_title(title)
    if trans:
        cset(m4trans=0)
        setup_dae_transmission()
        change_title(title+" TRANS")
        waitfor_move()
        begin()
        waitfor_frames(tot)
        end()
    else:
        cset(m4trans=200)
        waitfor_move()
        pol_run(u, d, tot)

def RFflipper_on(current=6.0):
    """Supply Power to the RFflipper.  This command should not be used for setting the flipper state"""
    set_pv("IN:LARMOR:SPINFLIPPER_01:FLIPSTATE:SP", 1)
    time.sleep(1)
    set_pv("IN:LARMOR:SPINFLIPPER_01:FLIPCURR:SP", str(current))
    time.sleep(3)
    irms=get_pv("IN:LARMOR:SPINFLIPPER_01:FLIPCURR")
    print('RF Flipper on at irms='+str(irms))

def waitfor_arm(arm=1):
    armstate=get_pv("TE:LARMOR:SIMARRIVED")
    k=0
    while armstate == 'Yes':
        time.sleep(5)
        armstate=get_pv("TE:LARMOR:SIMARRIVED")
        k+=1
        if (k > 60):
            #Time out of loop
            break
    k=0
    while armstate == 'No':
        time.sleep(5)
        armstate=get_pv("TE:LARMOR:SIMARRIVED")
        k+=1
        if (k > 60):
            #Time out of loop
            break

def calc_pso(thetaval=-45): 
    if thetaval < 0:
        psoval=0.0292*thetaval*thetaval+5.5057*thetaval+278.59
        return psoval
    else:
        print("Theta Value provided is greater than 0")
        print("This is the value for -45deg")
        return 90
        
def theta_near(angle):
    for i in range(1, 5):
        if np.abs(angle-cget("Mag{}_Theta".format(i))["value"]) > 0.1:
            return False
    return True
    
def get_PSO(magnet):
    return cget("Mag{}_Ty2".format(magnet))["value"]-cget("Mag{}_Ty1".format(magnet))["value"]-2*190.5
    
def pso_near(pso):
    for i in range(1, 5):
        if np.abs(pso-get_PSO(i)) > 0.2:
            return False
    return True
    
def get_L2():
    return np.abs(cget("Mag4_Tx0")["value"] - cget("Mag3_Tx0")["value"])
    
def set_L1(l1):
    if(get_pv("TE:LARMOR:SIMARM12")!='Arm1'):
        set_pv("TE:LARMOR:SIMARM12:SP",1)
    time.sleep(2)
    set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    if(get_pv("TE:LARMOR:SIMSIM")=='Yes'):
        set_pv("TE:LARMOR:SIMSIM:SP",0)
    time.sleep(2)
    set_pv("TE:LARMOR:SIMERRORCLEAR:SP",1)
    time.sleep(2)
    cset(SimL1=l1)
    time.sleep(2)
    set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    # After Jan 2018 update change to SIMMOVE
    #set_pv("TE:LARMOR:SIMGO:SP",1)
    set_pv("TE:LARMOR:SIMMOVE:SP",1)
    waitfor_arm()
    time.sleep(3)

def set_L2(l2):
    if(get_pv("TE:LARMOR:SIMARM12")!='Arm2'):
        set_pv("TE:LARMOR:SIMARM12:SP",0)
    time.sleep(2)
    set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    if(get_pv("TE:LARMOR:SIMSIM")=='Yes'):
        set_pv("TE:LARMOR:SIMSIM:SP",0)
    time.sleep(2)
    set_pv("TE:LARMOR:SIMERRORCLEAR:SP",1)
    time.sleep(2)
    cset(SimL2=l2)
    time.sleep(2)
    set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    # After Jan 2018 update change to SIMMOVE
    #set_pv("TE:LARMOR:SIMGO:SP",1)
    set_pv("TE:LARMOR:SIMMOVE:SP",1)
    waitfor_arm()
    time.sleep(3)
    
def l2_near(l2):
    return np.abs(l2-get_L2()) <= 0.025

def park_arm1():
    set_pv("TE:LARMOR:MOTOR1B:POS:SP",-63.439)
    set_pv("TE:LARMOR:MOTOR2B:POS:SP",-63.439)
    set_pv("TE:LARMOR:MOTOR1C:POS:SP",-370)
    set_pv("TE:LARMOR:MOTOR2C:POS:SP",-370)
    set_pv("TE:LARMOR:MOTOR1E:POS:SP",370)
    set_pv("TE:LARMOR:MOTOR2E:POS:SP",370)
    set_pv("TE:LARMOR:MOTOR1B:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR2B:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR1C:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR2C:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR1E:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR2E:MOVE:SP",1)

def park_arm2_part1():
    # Initial set of moves to park the second arm safely
    set_pv("TE:LARMOR:MOTOR3A:POS:SP",-1205.0)
    set_pv("TE:LARMOR:MOTOR3B:POS:SP",-63.435)
    set_pv("TE:LARMOR:MOTOR3C:POS:SP",-370)
    set_pv("TE:LARMOR:MOTOR3E:POS:SP",370)
    set_pv("TE:LARMOR:MOTOR3A:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR3B:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR3C:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR3E:MOVE:SP",1)

    set_pv("TE:LARMOR:MOTOR4A:POS:SP",-1405.0)
    set_pv("TE:LARMOR:MOTOR4B:POS:SP",-63.435)
    set_pv("TE:LARMOR:MOTOR4C:POS:SP",-370)
    set_pv("TE:LARMOR:MOTOR4E:POS:SP",370)
    set_pv("TE:LARMOR:MOTOR4A:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR4B:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR4C:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR4E:MOVE:SP",1)
    
def set_poleshoe_angle2(theta,l2,MHz=1):
    pso=calc_pso(theta)
    
    # May 2022 L2 changed after modifications to gradient coils
    #if l2 > 1187 and l2 < 1191:
    # add in a frequency dependent distance
    if MHz==0.5:
        if l2 > 1161 and l2 < 1166:
            m3tx0=cget('Mag3_Tx0')['value']
            m4tx0=cget('Mag4_Tx0')['value']
            l2calc=m3tx0-m4tx0
            print(l2calc)
            if np.abs(l2-l2calc) > 0.025:
                set_pv("TE:LARMOR:MOTOR4A:POS:SP",m3tx0-l2)
    if MHz==1:
        if l2 > 1167 and l2 < 1172:
            m3tx0=cget('Mag3_Tx0')['value']
            m4tx0=cget('Mag4_Tx0')['value']
            l2calc=m3tx0-m4tx0
            print(l2calc)
            if np.abs(l2-l2calc) > 0.025:
                set_pv("TE:LARMOR:MOTOR4A:POS:SP",m3tx0-l2)
    if MHz==2:
        if l2 > 1173 and l2 < 1179:
            m3tx0=cget('Mag3_Tx0')['value']
            m4tx0=cget('Mag4_Tx0')['value']
            l2calc=m3tx0-m4tx0
            print(l2calc)
            if np.abs(l2-l2calc) > 0.025:
                set_pv("TE:LARMOR:MOTOR4A:POS:SP",m3tx0-l2)
    
    # assuming we need to move something set everything by script
    if theta <= -25 and theta > -90.1:
        # change the value of simtheta so that the logs are correct
        cset(SimTheta=theta)
        set_pv("TE:LARMOR:MOTOR1B:POS:SP",theta)
        set_pv("TE:LARMOR:MOTOR2B:POS:SP",theta)
        set_pv("TE:LARMOR:MOTOR3B:POS:SP",theta)
        set_pv("TE:LARMOR:MOTOR4B:POS:SP",theta)
    else:
        print("Theta is out of range")
        return
    
    if pso > 19.58:
        ty1=190.5+0.5*pso
        set_pv("TE:LARMOR:MOTOR1C:POS:SP",-ty1)
        set_pv("TE:LARMOR:MOTOR2C:POS:SP",-ty1)
        set_pv("TE:LARMOR:MOTOR3C:POS:SP",-ty1)
        set_pv("TE:LARMOR:MOTOR4C:POS:SP",-ty1)
        set_pv("TE:LARMOR:MOTOR1E:POS:SP",ty1)
        set_pv("TE:LARMOR:MOTOR2E:POS:SP",ty1)
        set_pv("TE:LARMOR:MOTOR3E:POS:SP",ty1)
        set_pv("TE:LARMOR:MOTOR4E:POS:SP",ty1)
    else:
        return
    
    set_pv("TE:LARMOR:MOTOR4A:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR1B:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR2B:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR3B:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR4B:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR1C:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR2C:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR3C:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR4C:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR1E:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR2E:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR3E:MOVE:SP",1)
    set_pv("TE:LARMOR:MOTOR4E:MOVE:SP",1)
    
    for i in range(1,5):
        while True:
            time.sleep(1)
            if l2 > 1161 and l2 < 1172:
                if np.abs(get_pv("TE:LARMOR:MOTOR4A:POS") - (m3tx0-l2) ) > .05:
                    continue
            if np.abs(get_pv("TE:LARMOR:MOTOR{}C:POS".format(i)) + ty1) > .05:
                continue
            if np.abs(get_pv("TE:LARMOR:MOTOR{}E:POS".format(i)) - ty1) > .05:
                continue
            if np.abs(get_pv("TE:LARMOR:MOTOR{}B:POS".format(i)) - theta) > .05:
                continue
            break

def set_poleshoe_angle(theta, l2, MHz=None):
    pso=calc_pso(theta)
    if MHz:
        set_DCFields(MHz)
    
    if theta_near(theta) and pso_near(pso):
        if not l2_near(l2):
            set_L2(l2)
        return
            
        
    print("pso value will be set to "+str(pso)+"mm")
    if(get_pv("TE:LARMOR:SIMARM12")!='Arm2'):
        set_pv("TE:LARMOR:SIMARM12:SP",0)
    time.sleep(2)
    set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    if(get_pv("TE:LARMOR:SIMSIM")=='Yes'):
        set_pv("TE:LARMOR:SIMSIM:SP",0)
    # clear possible motion control errors
    time.sleep(2)
    set_pv("TE:LARMOR:SIMERRORCLEAR:SP",1)
    time.sleep(2)
    
    # After Jan 2018 Update remove this check
    '''
    if (pso < 110):
        cset(SimPSO=110) # Open pole shoe to satisfy collision solver
    else:    
        if not pso_near(pso):
            cset(SimPSO=pso)
    '''
    if not pso_near(pso):
        cset(SimPSO=pso)
    cset(SimTheta=theta)
    cset(SimL2=l2)
    time.sleep(2)
    set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    # After Jan 2018 update change to SIMMOVE
    #set_pv("TE:LARMOR:SIMGO:SP",1)
    set_pv("TE:LARMOR:SIMMOVE:SP",1)
    waitfor_arm()
    time.sleep(3)
    
    # Now do Arm 1
    set_pv("TE:LARMOR:SIMARM12:SP",1)
    time.sleep(5)
    set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    # clear possible motion control errors
    set_pv("TE:LARMOR:SIMERRORCLEAR:SP",1)
    time.sleep(2)
    # After Jan 2018 update change to SIMMOVE
    #set_pv("TE:LARMOR:SIMGO:SP",1)
    set_pv("TE:LARMOR:SIMMOVE:SP",1)
    time.sleep(2)
    set_pv("TE:LARMOR:SIMGO:SP",1)
    waitfor_arm()

    # After Jan 2018 update remove this
    '''
    if (pso < 110):
        cset(SimPSO=pso)
        time.sleep(2)
        set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
        time.sleep(2)
        set_pv("TE:LARMOR:SIMGO:SP",1)
        waitfor_arm()
        time.sleep(3)# Now do Arm 2
        set_pv("TE:LARMOR:SIMARM12:SP",0)
        time.sleep(2)
        set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
        time.sleep(2)
        time.sleep(2)
        # After Jan 2018 update change to SIMMOVE
        #set_pv("TE:LARMOR:SIMGO:SP",1)
        set_pv("TE:LARMOR:SIMMOVE:SP",1)
        waitfor_arm()
    '''
    
    
def set_DCFields(MHz=1):
    if MHz == 0.5:
        '''
        cset(DCMagField1=17.14)
        time.sleep(0.5)
        cset(DCMagField2=17.14)
        time.sleep(0.5)
        cset(DCMagField3=-17.14)
        time.sleep(0.5)
        cset(DCMagField4=-17.30)
        '''
        cset(DCMagField1=17.25)
        time.sleep(0.5)
        cset(DCMagField2=17.25)
        time.sleep(0.5)
        cset(DCMagField3=-17.4)
        time.sleep(0.5)
        cset(DCMagField4=-17.4)
    if MHz == 1:
        # fields modified May 2022 after changes to the gradient coils
        '''
        cset(DCMagField1=34.28)
        time.sleep(0.5)
        cset(DCMagField2=34.28)
        time.sleep(0.5)
        cset(DCMagField3=-34.28)
        time.sleep(0.5)
        cset(DCMagField4=-34.6)
        '''
        cset(DCMagField1=34.5)
        time.sleep(0.5)
        cset(DCMagField2=34.5)
        time.sleep(0.5)
        cset(DCMagField3=-34.8)
        time.sleep(0.5)
        cset(DCMagField4=-34.8)
    if MHz == 2:
        '''
        cset(DCMagField1=68.56)
        time.sleep(0.5)
        cset(DCMagField2=68.56)
        time.sleep(0.5)
        cset(DCMagField3=-68.56)
        time.sleep(0.5)
        cset(DCMagField4=-69.2)
        '''
        cset(DCMagField1=69)
        time.sleep(0.5)
        cset(DCMagField2=69)
        time.sleep(0.5)
        cset(DCMagField3=-69.6)
        time.sleep(0.5)
        cset(DCMagField4=-69.6)
        
    if MHz == 3:
        cset(DCMagField1=3*34.28)
        time.sleep(0.5)
        cset(DCMagField2=3*34.28)
        time.sleep(0.5)
        cset(DCMagField3=-3*34.28)
        time.sleep(0.5)
        cset(DCMagField4=-3*34.6)

def cset_str(blockString, value):
        dict = {blockString: value}
        gen.cset(**dict)

def echoscan_axis(axis,startval,endval,npoints,frms,rtitle,save=False,usered=0):
    """
    Perform an echo scan on a given instrument parameter
    
    Parameters
    ==========
    axis
      The motor axis to scan, as a string.  You likely was "Echo_Coil_SP"
    startval
      The first value of the scan
    endval
      The last value of the scan
    npoints
      The number of points for the scan. This is one more than the number of steps
    frms
      The number of frames per spin state.  There are ten frames per second
    rtitle
      The title of the run.  This is important when the run is saved
    save
      If True, save the scan in the log.
    usered
      If True, only use the low wavelengths to set the centre
      
    Returns
    =======
    The best fit for the center of the echo value.
    """
    
    
    from scipy.optimize import curve_fit
    
    abort()

    #setup_dae_scanning12()
    #  force the setup for alanis to get the detector and spectra tables right as Adam's code tries to be to clever....
    gen.change(nperiods=1)
    gen.change_start()
    gen.change_tables(detector=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\Alanis_Detector.dat")
    gen.change_tables(spectra=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\spectra_scanning_Alanis.dat")
    #gen.change_tables(spectra=r"C:\Instrument\Settings\Tables\spectra_scanning_12.dat")
    gen.change_tables(wiring=r"C:\Instrument\Settings\config\NDXLARMOR\configurations\tables\Alanis_Wiring_dae3.dat")
    gen.change_tcb(low=5.0,high=100000.0,step=100.0,trange=1,log=0)
    gen.change_finish()

    
    gen.change(title=rtitle)
    gen.change(nperiods=npoints*2)
    
    gen.begin(paused=1)
    # setup the scan arrays and figure
    xval=[0]*npoints
    yval=[0]*npoints
    eval=[0]*npoints

    stepsize=(endval-startval)/float(npoints-1)
    for i in range(npoints):
        xval[i]=(startval+i*stepsize)

    mpl.ion()
    fig1=mpl.figure(1)
    mpl.clf()
    ax = mpl.subplot(111)
    #ax.set_xlim((0,4))
    ax.set_xlabel(axis)
    ax.set_ylabel('Neutron Polarisation')
    # reasonable x-Axis, necessary to get the full window from the first datapoint
    scanrange = np.absolute(endval - startval)
    mpl.xlim((startval-scanrange*0.05, endval+scanrange*0.05))
    mpl.draw()
    mpl.pause(0.001)
    flipper1(1)
    
    colors = ['ko', "r^", "gd", "bs"]
    
    for i in range(npoints):
        gen.change(period=(i*2)+1)
        cset_str(axis,xval[i])
        sleep(3)
        flipper1(1)
        gen.waitfor_move()
        gfrm=gen.get_frames()
        resume()
        gen.waitfor(frames=gfrm+frms)
        pause()
        flipper1(0)
        gen.change(period=(i*2)+2)
        gfrm=gen.get_frames()
        resume()
        gen.waitfor(frames=gfrm+frms)
        pause()
        
        # wavelength range 1 3-5Ang
        a1=gen.get_spectrum(1,(i*2)+1)
        msigup=sum(a1['signal'])*100.0
        mesigup=(np.sqrt(msigup))
        
        a1=gen.get_spectrum(1,(i*2)+2)
        msigdo=sum(a1['signal'])*100.0
        mesigdo=(np.sqrt(msigdo))

        sigup = []
        sigdo = []
        for slc in [slice(222,666), slice(222, 370), slice(370, 518), slice(518, 666)]:
        #for slc in [slice(222,518), slice(222, 370), slice(370, 518)]:
            '''
            a1=gen.get_spectrum(11,(i*2)+1)
            sigdo.append(sum(a1['signal'][slc])*100.0)
            a1=gen.get_spectrum(12,(i*2)+1)
            sigdo[-1] += sum(a1['signal'][slc])*100.0

            a1=gen.get_spectrum(11,(i*2)+2)
            sigup.append(sum(a1['signal'][slc])*100.0)
            a1=gen.get_spectrum(12,(i*2)+2)
            sigup[-1] += sum(a1['signal'][slc])*100.0
            '''
            # using alanis so only take spectrum 12
            a1=gen.get_spectrum(12,(i*2)+1)
            sigdo.append(sum(a1['signal'][slc])*100.0)
            a1=gen.get_spectrum(12,(i*2)+2)
            sigup.append(sum(a1['signal'][slc])*100.0)
            
        sigup = np.array(sigup, dtype=np.float64)
        sigdo = np.array(sigdo, dtype=np.float64)
        esigdo = np.sqrt(sigdo)
        esigup = np.sqrt(sigup)
        print("--------")
        print(xval[i])
        print(sigup)
        print(sigdo)
        
        yval[i]=(sigup-sigdo)/(sigup+sigdo)
        eval[i]=yval[i]*np.sqrt(esigdo**2+esigup**2)*np.sqrt((sigup-sigdo)**-2+(sigup+sigdo)**-2)
        #eval[i]=yval[i]*np.sqrt(esido**2+esidup**2)*np.sqrt((sigup-sigdn)**-2+(sigup+sigdn)**-2)
        #eval[i]=yval[i]*1e-3
        #eval[i]=(sqrt((sig/(msig*msig))+(sig*sig/(msig*msig*msig))))
        for idx, clr in enumerate(colors):
            ax.errorbar(xval[i], yval[i][idx], eval[i][idx], fmt = clr)
            if i > 0:
                ax.plot([xval[i-1], xval[i]], [yval[i-1][idx], yval[i][idx]], clr[0])
        fig1.canvas.draw()
        mpl.pause(0.001)
    if save:
        end()
    else:
        abort()
    
    xval = np.array(xval)
    yval = np.array(yval)
    eval = np.array(eval)
    
    print(xval.shape)
    print(yval.shape)
    print(eval.shape)
    
    def model(x, center, amp, freq, width):
        return amp * np.cos((x-center)*freq)*np.exp(-((x-center)/width)**2)
        
    # popt, _ = curve_fit(model, xval, yval[:, 0], [6.5, 1, 1, 10], sigma=eval[:, 0])
    # ax.plot(xval, model(xval, *popt), "-")
    # fig1.canvas.draw()
    # print("The center is {}".format(popt[0]))
    
    centers = []
    xplot = np.linspace(np.min(xval), np.max(xval), 1001)
    guess = xval[np.argmax(yval[:, 0])]
    popt = [guess, 1, 2*np.pi/(750.0), endval-startval]
    mpl.clf()
    ax = mpl.subplot(111)
    #ax.set_xlim((0,4))
    ax.set_xlabel(axis)
    ax.set_ylabel('Neutron Polarisation')
    for i in range(yval.shape[1]):
        popt, _ = curve_fit(model, xval, yval[:, i], popt, sigma=eval[:, 0])
        ax.errorbar(xval, yval[:, i], yerr=eval[:, i], fmt=colors[i])
        ax.plot(xplot, model(xplot, *popt), colors[i][:-1]+"-")
        centers.append(popt[0])
    fig1.canvas.draw()
    mpl.pause(0.001)
    
    if usered == True:
        value=centers[0]
        error=0.0
    else:
        value = np.mean(centers)
        error = np.std(centers)
        digits = -1*int(np.floor(np.log(error)/np.log(10)))
        value = np.around(value, digits)
        error = np.around(error, digits)
    print("The center is {} +- {}".format(value, error))
    mpl.ioff()
    return (value, error)
    
def auto_tune(axis, *args, **kwargs):
    """
    Perform an echo scan on a given instrument parameter, then set
    the instrument to echo.
    
    Parameters
    ==========
    axis
      The motor axis to scan, as a string.  You likely was "Echo_Coil_SP"
    startval
      The first value of the scan
    endval
      The last value of the scan
    npoints
      The number of points for the scan. This is one more than the number of steps
    frms
      The number of frames per spin state.  There are ten frames per second
    rtitle
      The title of the run.  This is important when the run is saved
    save
      If True, save the scan in the log.
    usered
      If True, only use the low wavelengths to set the centre
      
    Returns
    =======
    The best fit for the center of the echo value.
    """
    cset(m4trans=200)
    waitfor_move()
    center, error = echoscan_axis(axis, *args, **kwargs)
    if error >= 40:
        return False
    cset_str(axis, center)
    return True
    
def auto_tune_2(axis, startval, endval, npoints, frms=50, rtitle="Echo Scan", save=False):
    """
    Perform an echo scan on a given instrument parameter, then set
    the instrument to echo.
    
    Parameters
    ==========
    axis
      The motor axis to scan, as a motion object.  You likely want Echo_Coil_SP
    startval
      The first value of the scan
    endval
      The last value of the scan
    npoints
      The number of points for the scan. This is one more than the number of steps
    frms
      The number of frames per spin state.  There are ten frames per second
    rtitle
      The title of the run.  This is important when the run is saved
    save
      If True, save the scan in the log.
      
    Returns
    =======
    The best fit for the center of the echo value.
    """
    result = ls.scan(axis, startval, endval, npoints).fit(
        DampedOscillator, frames=frms, detector=ls.pol_measure)
    axis(result["center"])
	
def pol_run(u=2000,d=2000,total=36000, dae_setting=0):
    if dae_setting==0:
        setup_dae_event()
    elif dae_setting==1:
        setup_dae_scanning12()
    change(nperiods=2)
    begin(paused=1)
    gfrm=get_frames()
    
    while gfrm < total:
        change(period=1)
        flipper1(1)
        gfrm=get_frames()
        resume()
        waitfor(frames=gfrm+u)
        pause()

        change(period=2)
        flipper1(0)
        gfrm=get_frames()
        resume()
        waitfor(frames=gfrm+d)
        pause()

        gfrm=get_frames()
    end()

def angle_and_tune(theta, scan_range=(5000,7800), l2=1188, pts=37, save=True, mhz=None):
    for retries in range(2):
        #l2=1188 is the best value for 1 MHz
        #l2=1179 is the best value for 0.5 MHz
        #set_poleshoe_angle(theta=theta,l2=l2)
        set_poleshoe_angle(theta=theta,l2=l2, MHz=mhz)
        #set_poleshoe_angle(theta=theta,l2=1179)
        if theta_near(theta):
            break
            
    #new_set_pos(2)
    auto_tune("Echo_Coil_SP", scan_range[0], scan_range[1], pts, 50, "Echo scan at {} degrees".format(theta), save)
    