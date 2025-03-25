# speed_control.py takes target speeds and generates duty cycles
# to send to motors, and has a function to execute PID control.

# Import external libraries
import numpy as np                                  # for handling arrays

# Import local files
import motor as m                               # for controlling motors

# Initialize variables
u_integral = 0
phi_max = 7.
DRS = 1.0                                           # direct rescaling - for open-loop motor duty

kp_left = 0.04                                           # proportional term
ki_left = 0.04                                           # integral term
kd_left = 0.04                                            # derivative term

kp_right = 0.04                                           # proportional term
ki_right = 0.04                                           # integral term
kd_right = 0.04                                            # derivative term
pidGains = np.array([[kp_left, kp_right], 
                     [ki_left, ki_right], 
                     [kd_left, kd_right]])                   # form an array to collect pid gains.

# a function for converting target rotational speeds to PWMs without feedback
def openLoop(pdl, pdr):
    duties = np.array([pdl, pdr])                   # put the values into an array
    duties = duties * 1/phi_max * DRS               # rescaling. 1=max PWM, 7. = max rad/s achievable
    duties[0] = sorted([-0.99, duties[0], 0.99])[1] # place bounds on duty cycle
    duties[1] = sorted([-0.99, duties[1], 0.99])[1] # place bounds on duty cycle
    return duties

def scalingFunction(x):                             # a fcn to compress the PWM region where motors don't turn
    if -0.222 < x and x < 0.222:
        y = (x * 3)
    elif x > 0.222:
        y = ((x * 0.778) + 0.222)
    else:
        y = ((x * 0.778) - 0.222)
    return y

def scaleMotorEffort(u):                            # send the control effort signals to the scaling function
    u_out = np.zeros(2)
    u_out[0] = scalingFunction(u[0])
    u_out[1] = scalingFunction(u[1])
    return(u_out)

def driveOpenLoop(pdTargets):                       # Pass Phi dot targets to this function
    duties = openLoop(pdTargets[0], pdTargets[1])   # produce duty cycles from the phi dots
    m.driveLeft(duties[0])                           # send command to motors
    m.driveRight(duties[1])                          # send command to motors

def driveClosedLoop(pdt, pdc, de_dt):               # this function runs motors for closed loop PID control
    global u_integral
    e = np.array(pdt - pdc)                                 # compute error

    kp = pidGains[0]                                # gains are input as constants, above
    ki = pidGains[1]
    kd = pidGains[2]

    # GENERATE COMPONENTS OF THE CONTROL EFFORT, u
    u_proportional = (e * kp)                                       # proportional term
    try:
        u_integral += (e * ki)                                      # integral term
    except:
        u_integral = (e * ki)                                       # for first iteration, u_integral does not exist

    u_derivative = (de_dt * kd)                                     # derivative term takes de_dt as an argument

    # CONDITION THE SIGNAL BEFORE SENDING TO MOTORS
    u = np.round((u_proportional + u_integral + u_derivative), 2)   # must round to ensure driver handling
    #u = scaleMotorEffort(u)                                         # perform scaling - described above
    u[0] = sorted([-1, u[0], 1])[1]                                 # place bounds on the motor commands
    u[1] = sorted([-1, u[1], 1])[1]                                 # within [-1, 1]

    # SEND SIGNAL TO MOTORS
    m.driveLeft(round(u[0], 2))                                        # must round to ensure driver handling!
    m.driveRight(round(u[1], 2))                                        # must round to ensure driver handling!
    return
