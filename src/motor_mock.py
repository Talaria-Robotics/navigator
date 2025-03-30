import threading
import time
import numpy as np
from encoder_mock import readShaftPositions, setMockReading, encL, encR

# Max motor speed
max_rpm = 200.0
max_degs = 1200.0
max_rads = 20.943951

# Mock PWM channels
channels = {
    "left_chA": 0.0,
    "left_chB": 0.0,
    "right_chA": 0.0,
    "right_chB": 0.0,
}

def _updateEncoders(channels: dict[str, float]):
    time_previous = time.time()
    while True:
        time_now = time.time()
        deltaTime = time_now - time_previous
        if deltaTime == 0.0:
            continue

        left_chA, right_chA = channels["left_chA"], channels["right_chA"]

        max_speedL, max_speedR = left_chA * max_degs, right_chA * max_degs
        deltaAngL, deltaAngR = max_speedL * deltaTime, max_speedR * deltaTime
        angL, angR = readShaftPositions()

        setMockReading(encL, angL + deltaAngL)
        setMockReading(encR, angR + deltaAngR)

        time_previous = time_now

thread = threading.Thread(target=_updateEncoders, args=(channels,))
thread.start()

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
    channels["left_chB"] = motorPWM[0]
    channels["left_chA"] = motorPWM[1]

def driveRight(speed: float):
    motorPWM = computePWM(speed)
    channels["right_chB"] = motorPWM[0]
    channels["right_chA"] = motorPWM[1]

def drive(speed: float):
    driveLeft(speed)
    driveRight(speed)

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
