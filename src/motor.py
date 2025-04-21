from gpiozero import PWMOutputDevice as pwm
import time
import numpy as np

isInitialized: bool = False

# Motor driving frequency
frq = 150

# GPIO pin numbering
left_chA: pwm
left_chB: pwm
right_chA: pwm
right_chB: pwm

def initMotors():
    global isInitialized
    if isInitialized:
        return
    
    isInitialized = True

    global left_chA, left_chB, right_chA, right_chB
    left_chA = pwm(17, frequency=frq, initial_value=0)
    left_chB = pwm(18, frequency=frq, initial_value=0)
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

def driveLeft(speed: float):
    motorPWM = computePWM(speed)
    left_chB.value = motorPWM[0]
    left_chA.value = motorPWM[1]

def driveRight(speed: float):
    motorPWM = computePWM(speed)
    right_chB.value = motorPWM[0]
    right_chA.value = motorPWM[1]

def drive(speed: float):
    motorPWM = computePWM(speed)
    left_chB.value = motorPWM[0]
    left_chA.value = motorPWM[1]
    right_chB.value = motorPWM[0]
    right_chA.value = motorPWM[1]

if __name__ == "__main__":
    while True:
        print("Driving forward")
        drive(0.8)
        time.sleep(4)

        print("Driving backward")
        drive(-0.8)
        time.sleep(4)
        
        print("I'll try spinning, that's a good trick!")
        driveLeft(1.0)
        driveRight(-1.0)
        time.sleep(4)
        
        print("Stopping motors")
        drive(0)
        time.sleep(4)
