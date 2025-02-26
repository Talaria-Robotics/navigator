from gpiozero import PWMOutputDevice as pwm
import time
import numpy as np

# Motor driving frequency
frq = 150

# GPIO pin numbering
left_chA  = pwm(17, frequency=frq, initial_value=0)
left_chB  = pwm(18, frequency=frq, initial_value=0)
right_chA = pwm(22, frequency=frq, initial_value=0)
right_chB = pwm(23, frequency=frq, initial_value=0)

# Speed percentage, in range [-1,1]
def computePWM(speed: float) -> tuple[float, float]:
    if speed == 0:
        return 0, 0
    else:
        # Shift range to [0,2]
        x = speed + 1.0
        
        # Channel A sweeps low to high
        chA = 0.5 * x
        chA = np.round(chA, 2)
        
        # Channel B sweeps high to low
        chB = 1 - (0.5 * x)
        chB = np.round(chB, 2)
        
        return chA, chB
"""
def sendLeft(mySpeed: float):
    myPWM = computePWM(mySpeed)
    left_chB.value = myPWM[0]
    left_chA.value = myPWM[1]

def sendRight(mySpeed: float):
    myPWM = computePWM(mySpeed)
    right_chB.value = myPWM[0]
    right_chA.value = myPWM[1]
"""
def drive(mySpeed: float):
    myPWM = computePWM(mySpeed)
    left_chB.value = myPWM[0]
    left_chA.value = myPWM[1]
    right_chB.value = myPWM[0]
    right_chA.value = myPWM[1]

if __name__ == "__main__":
    while True:
        print("Driving left motor")
        # sendLeft(0.8)
        # sendRight(0.8)
        drive(0.8)
        time.sleep(4)

        print("Driving right motor")
        # sendLeft(-0.8)
        # sendRight(-0.8)
        drive(-0.8)
        time.sleep(4)
        
        print("Stopping motors")
        # sendLeft(0)
        # sendRight(0)
        drive(0)
        time.sleep(4)
