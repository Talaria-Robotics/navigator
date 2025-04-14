from odometry import computeWheelAnglesForForward, computeDeltaThetaDeg
from path_following import isTargetReached
from encoder import readShaftPositions
from motor import driveLeft, driveRight, drive
from lidar import getNearest, init, disconnect
from time import sleep
import numpy as np

def driveToAngularDisplacement(targetAngDispL: float, targetAngDispR: float):
    angDispSignL, angDispSignR = np.sign(targetAngDispL), np.sign(targetAngDispR)

    dutyCycle = 0.8
    if angDispSignL != angDispSignR:
        dutyCycle = 1.0

    motorSpeedL, motorSpeedR = dutyCycle * angDispSignL, dutyCycle * angDispSignR
    
    doneL, doneR = False, False
    angDispL, angDispR = 0, 0
    
    lastAngleL, lastAngleR = readShaftPositions()
    lastTargetDeltaL, lastTargetDeltaR = np.nan, np.nan

    init()

    try:
        print("Entering step loop...")
        while not (doneL and doneR):
            angleL, angleR = readShaftPositions()
            
            # Handle when angle overflows (crossing 0 deg)
            dThetaL = computeDeltaThetaDeg(lastAngleL, angleL)
            angDispL += dThetaL

            dThetaR = computeDeltaThetaDeg(lastAngleR, angleR)
            angDispR += dThetaR
            #print(f"Delta Theta: {dThetaL:.1f} {dThetaR:.1f}")

            # Compute the remaining angular displacement
            targetDeltaL, targetDeltaR = targetAngDispL - angDispL, targetAngDispR - angDispR
            print(f"Disp remaining: {targetDeltaL:.1f} {targetDeltaR:.1f}\t\t{motorSpeedL:.1f} {motorSpeedR:.1f}")

            if isTargetReached(lastTargetDeltaL, targetDeltaL, 0.01):
                doneL = True
                motorSpeedL = 0.0
            driveRight(motorSpeedL)

            if isTargetReached(lastTargetDeltaR, targetDeltaR, 0.01):
                doneR = True
                motorSpeedR = 0.0
            driveLeft(motorSpeedR)

            lastAngleL, lastAngleR = angleL, angleR
            lastTargetDeltaL, lastTargetDeltaR = targetDeltaL, targetDeltaR

            # DEMO
            # Check LIDAR for obstacles
            while True:
                nearestR, nearestAlpha = getNearest()
                nearestDist = abs(nearestR)
                if nearestDist > 6.0 or nearestDist < 0.01:
                    break

                # Obstacle within 6", wait!
                #drive(0)
            # END DEMO

            # Ensure the delta theta is greater than the error
            # in the encoder measurements
            sleep(0.05)
    except KeyboardInterrupt:
        drive(0)
        print("Navi: Stopping")
        raise
    finally:
        disconnect()


if __name__ == "__main__":
    maxAngularDisplacement, _ = computeWheelAnglesForForward(2 * 12)

    driveToAngularDisplacement(maxAngularDisplacement, maxAngularDisplacement)
