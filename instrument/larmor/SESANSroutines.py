import time as time
import numpy as np
import math
from matplotlib.pyplot import errorbar, plot, show
import matplotlib.pyplot as mpl
import technique.sans.genie as gen
from time import sleep


def RFflipper_on(current=6.0):
    """Supply Power to the RFflipper.  This command should not be used for
setting the flipper state"""
    gen.set_pv("IN:LARMOR:SPINFLIPPER_01:FLIPSTATE:SP", 1)
    time.sleep(1)
    gen.set_pv("IN:LARMOR:SPINFLIPPER_01:FLIPCURR:SP", str(current))
    time.sleep(3)
    irms=get_pv("IN:LARMOR:SPINFLIPPER_01:FLIPCURR")
    print('RF Flipper on at irms='+str(irms))


def flipper1(state=0):
    if state == 0:
        gen.set_pv("IN:LARMOR:SPINFLIPPER_01:FLIPSTATE:SP", 0)
    else:
        gen.set_pv("IN:LARMOR:SPINFLIPPER_01:FLIPSTATE:SP", 1)
    time.sleep(5)
    flipstate=get_pv("IN:LARMOR:SPINFLIPPER_01:FLIPSTATE")
    print("Flipstate="+str(flipstate))

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
        gen.set_pv("TE:LARMOR:SIMARM12:SP",1)
    time.sleep(2)
    gen.set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    if(get_pv("TE:LARMOR:SIMSIM")=='Yes'):
        gen.set_pv("TE:LARMOR:SIMSIM:SP",0)
    time.sleep(2)
    gen.set_pv("TE:LARMOR:SIMERRORCLEAR:SP",1)
    time.sleep(2)
    gen.cset(SimL1=l1)
    time.sleep(2)
    gen.set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    # After Jan 2018 update gen.change to SIMMOVE
    #set_pv("TE:LARMOR:SIMGO:SP",1)
    gen.set_pv("TE:LARMOR:SIMMOVE:SP",1)
    waitfor_arm()
    time.sleep(3)

def set_L2(l2):
    if(get_pv("TE:LARMOR:SIMARM12")!='Arm2'):
        gen.set_pv("TE:LARMOR:SIMARM12:SP",0)
    time.sleep(2)
    gen.set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    if(get_pv("TE:LARMOR:SIMSIM")=='Yes'):
        gen.set_pv("TE:LARMOR:SIMSIM:SP",0)
    time.sleep(2)
    gen.set_pv("TE:LARMOR:SIMERRORCLEAR:SP",1)
    time.sleep(2)
    gen.cset(SimL2=l2)
    time.sleep(2)
    gen.set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    # After Jan 2018 update gen.change to SIMMOVE
    #set_pv("TE:LARMOR:SIMGO:SP",1)
    gen.set_pv("TE:LARMOR:SIMMOVE:SP",1)
    waitfor_arm()
    time.sleep(3)

def l2_near(l2):
    return np.abs(l2-get_L2()) <= 0.025

def park_arm1():
    gen.set_pv("TE:LARMOR:MOTOR1B:POS:SP",-63.439)
    gen.set_pv("TE:LARMOR:MOTOR2B:POS:SP",-63.439)
    gen.set_pv("TE:LARMOR:MOTOR1C:POS:SP",-370)
    gen.set_pv("TE:LARMOR:MOTOR2C:POS:SP",-370)
    gen.set_pv("TE:LARMOR:MOTOR1E:POS:SP",370)
    gen.set_pv("TE:LARMOR:MOTOR2E:POS:SP",370)
    gen.set_pv("TE:LARMOR:MOTOR1B:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR2B:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR1C:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR2C:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR1E:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR2E:MOVE:SP",1)

def park_arm2_part1():
    # Initial set of moves to park the second arm safely
    gen.set_pv("TE:LARMOR:MOTOR3A:POS:SP",-1205.0)
    gen.set_pv("TE:LARMOR:MOTOR3B:POS:SP",-63.435)
    gen.set_pv("TE:LARMOR:MOTOR3C:POS:SP",-370)
    gen.set_pv("TE:LARMOR:MOTOR3E:POS:SP",370)
    gen.set_pv("TE:LARMOR:MOTOR3A:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR3B:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR3C:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR3E:MOVE:SP",1)

    gen.set_pv("TE:LARMOR:MOTOR4A:POS:SP",-1405.0)
    gen.set_pv("TE:LARMOR:MOTOR4B:POS:SP",-63.435)
    gen.set_pv("TE:LARMOR:MOTOR4C:POS:SP",-370)
    gen.set_pv("TE:LARMOR:MOTOR4E:POS:SP",370)
    gen.set_pv("TE:LARMOR:MOTOR4A:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR4B:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR4C:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR4E:MOVE:SP",1)

def set_poleshoe_angle2(theta):
    pso=calc_pso(theta)

    # assuming we need to move something set everything by script
    if theta <= -20 and theta > -90:
        gen.set_pv("TE:LARMOR:MOTOR1B:POS:SP",theta)
        gen.set_pv("TE:LARMOR:MOTOR2B:POS:SP",theta)
        gen.set_pv("TE:LARMOR:MOTOR3B:POS:SP",theta)
        gen.set_pv("TE:LARMOR:MOTOR4B:POS:SP",theta)
    else:
        print("Theta is out of range")
        return

    if pso > 19.58:
        ty1=190.5+0.5*pso
        gen.set_pv("TE:LARMOR:MOTOR1C:POS:SP",-ty1)
        gen.set_pv("TE:LARMOR:MOTOR2C:POS:SP",-ty1)
        gen.set_pv("TE:LARMOR:MOTOR3C:POS:SP",-ty1)
        gen.set_pv("TE:LARMOR:MOTOR4C:POS:SP",-ty1)
        gen.set_pv("TE:LARMOR:MOTOR1E:POS:SP",ty1)
        gen.set_pv("TE:LARMOR:MOTOR2E:POS:SP",ty1)
        gen.set_pv("TE:LARMOR:MOTOR3E:POS:SP",ty1)
        gen.set_pv("TE:LARMOR:MOTOR4E:POS:SP",ty1)
    else:
        return

    gen.set_pv("TE:LARMOR:MOTOR1B:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR2B:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR3B:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR4B:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR1C:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR2C:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR3C:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR4C:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR1E:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR2E:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR3E:MOVE:SP",1)
    gen.set_pv("TE:LARMOR:MOTOR4E:MOVE:SP",1)

    for i in range(1,5):
        while True:
            time.sleep(1)
            if np.abs(get_pv("TE:LARMOR:MOTOR{}C:POS".format(i)) + ty1) > .05:
                continue
            if np.abs(get_pv("TE:LARMOR:MOTOR{}E:POS".format(i)) - ty1) > .05:
                continue
            if np.abs(get_pv("TE:LARMOR:MOTOR{}B:POS".format(i)) - theta) > .05:
                continue
            break

def set_poleshoe_angle(theta, l2, MHz):
    pso=calc_pso(theta)
    set_DCFields(MHz)

    if theta_near(theta) and pso_near(pso):
        if not l2_near(l2):
            set_L2(l2)
        return


    print("pso value will be set to "+str(pso)+"mm")
    if(get_pv("TE:LARMOR:SIMARM12")!='Arm2'):
        gen.set_pv("TE:LARMOR:SIMARM12:SP",0)
    time.sleep(2)
    gen.set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    if(get_pv("TE:LARMOR:SIMSIM")=='Yes'):
        gen.set_pv("TE:LARMOR:SIMSIM:SP",0)
    # clear possible motion control errors
    time.sleep(2)
    gen.set_pv("TE:LARMOR:SIMERRORCLEAR:SP",1)
    time.sleep(2)

    # After Jan 2018 Update remove this check
    '''
    if (pso < 110):
        gen.cset(SimPSO=110) # Open pole shoe to satisfy collision solver
    else:
        if not pso_near(pso):
            gen.cset(SimPSO=pso)
    '''
    if not pso_near(pso):
        gen.cset(SimPSO=pso)
    gen.cset(SimTheta=theta)
    gen.cset(SimL2=l2)
    time.sleep(2)
    gen.set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    # After Jan 2018 update gen.change to SIMMOVE
    #set_pv("TE:LARMOR:SIMGO:SP",1)
    gen.set_pv("TE:LARMOR:SIMMOVE:SP",1)
    waitfor_arm()
    time.sleep(3)

    # Now do Arm 1
    gen.set_pv("TE:LARMOR:SIMARM12:SP",1)
    time.sleep(5)
    gen.set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
    time.sleep(2)
    # clear possible motion control errors
    gen.set_pv("TE:LARMOR:SIMERRORCLEAR:SP",1)
    time.sleep(2)
    # After Jan 2018 update gen.change to SIMMOVE
    #set_pv("TE:LARMOR:SIMGO:SP",1)
    gen.set_pv("TE:LARMOR:SIMMOVE:SP",1)
    time.sleep(2)
    gen.set_pv("TE:LARMOR:SIMGO:SP",1)
    waitfor_arm()

    # After Jan 2018 update remove this
    '''
    if (pso < 110):
        gen.cset(SimPSO=pso)
        time.sleep(2)
        gen.set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
        time.sleep(2)
        gen.set_pv("TE:LARMOR:SIMGO:SP",1)
        waitfor_arm()
        time.sleep(3)# Now do Arm 2
        gen.set_pv("TE:LARMOR:SIMARM12:SP",0)
        time.sleep(2)
        gen.set_pv("TE:LARMOR:SIMGOSESANS:SP",1)
        time.sleep(2)
        time.sleep(2)
        # After Jan 2018 update gen.change to SIMMOVE
        #set_pv("TE:LARMOR:SIMGO:SP",1)
        gen.set_pv("TE:LARMOR:SIMMOVE:SP",1)
        waitfor_arm()
    '''


def set_DCFields(MHz=1):
    if MHz == 0.5:
        gen.cset(DCMagField1=17.14)
        time.sleep(0.5)
        gen.cset(DCMagField2=17.14)
        time.sleep(0.5)
        gen.cset(DCMagField3=-17.14)
        time.sleep(0.5)
        gen.cset(DCMagField4=-17.30)
    if MHz == 1:
        gen.cset(DCMagField1=34.28)
        time.sleep(0.5)
        gen.cset(DCMagField2=34.28)
        time.sleep(0.5)
        gen.cset(DCMagField3=-34.28)
        time.sleep(0.5)
        gen.cset(DCMagField4=-34.6)
    if MHz == 2:
        gen.cset(DCMagField1=68.56)
        time.sleep(0.5)
        gen.cset(DCMagField2=68.56)
        time.sleep(0.5)
        gen.cset(DCMagField3=-68.56)
        time.sleep(0.5)
        gen.cset(DCMagField4=-69.2)

def cset_str(blockString, value):
        dict = {blockString: value}
        gen.cset(**dict)

def echoscan_axis(axis,startval,endval,npoints,frms,rtitle,save=False):
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

    Returns
    =======
    The best fit for the center of the echo value.
    """

    from scipy.optimize import curve_fit

    abort()
    lm.setuplarmor_echoscan()

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
    ax.set_ylabel('Neutorn Polarisation')
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
        flipper1(1)
        gen.waitfor_move()
        gfrm=gen.get_frames()
        gen.resume()
        gen.waitfor(frames=gfrm+frms)
        gen.pause()
        flipper1(0)
        gen.change(period=(i*2)+2)
        gfrm=gen.get_frames()
        gen.resume()
        gen.waitfor(frames=gfrm+frms)
        gen.pause()

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
            a1=gen.get_spectrum(11,(i*2)+1)
            sigup.append(sum(a1['signal'][slc])*100.0)
            a1=gen.get_spectrum(12,(i*2)+1)
            sigup[-1] += sum(a1['signal'][slc])*100.0

            a1=gen.get_spectrum(11,(i*2)+2)
            sigdo.append(sum(a1['signal'][slc])*100.0)
            a1=gen.get_spectrum(12,(i*2)+2)
            sigdo[-1] += sum(a1['signal'][slc])*100.0
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

    Returns
    =======
    The best fit for the center of the echo value.
    """
    gen.cset(m4trans=200)
    gen.waitfor_move()
    center, error = echoscan_axis(axis, *args, **kwargs)
    if error >= 40:
        return False
    cset_str(axis, center)
    return True

def pol_run(u=2000,d=2000,total=36000, dae_setting=0):
    if dae_setting==0:
        lm.setuplarmor_event()
    elif dae_setting==1:
        lm.setuplarmor_echoscan()
    gen.change(nperiods=2)
    gen.begin(paused=1)
    gfrm=get_frames()

    while gfrm < total:
        gen.change(period=1)
        flipper1(1)
        gfrm=get_frames()
        gen.resume()
        gen.waitfor(frames=gfrm+u)
        gen.pause()

        gen.change(period=2)
        flipper1(0)
        gfrm=get_frames()
        gen.resume()
        gen.waitfor(frames=gfrm+d)
        gen.pause()

        gfrm=get_frames()
    end()

def angle_and_tune(theta, scan_range=(5000,7800), l2=1188, pts=37, save=True, mhz=1):
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
