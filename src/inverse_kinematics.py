# inverse_kinematics.py calculates wheel speeds from chassis speeds
# Calculations will intake motion requests in [theta, x] (rad, m)
# and output motion requests in [phi dot Left, pi dot right] (rad/s).
# This program runs on SCUTTLE with any CPU. 

# Import external libraries
import numpy as np                          # to perform matrix operations
import time

# define robot geometry
# Tread height = 2 5/16"
# Wheelbase width = 23 1/8"
R = 1.15625                           # wheel radius
L = 11.5625                           # half of the wheelbase
KWB = 10.00                           # (L / R) Wheel revolutions per body revolution
A = np.array([[1/R, -KWB], 
              [1/R, KWB]])          # matrix A * [xd, td] = [pdl, pdr]

# constants
twoPi = 2 * np.pi
fourPiSq = twoPi * twoPi

# define constraints for x_dot and theta_dot
max_xd = 0.4                        # maximum achievable x_dot (m/s), forward speed
max_td = (max_xd / L)               # maximum achievable theta_dot (rad/s), rotational speed

def computeWheelAnglesForTurn(bodyAngle: float) -> tuple[float, float]:
    """
    Effectively converts a body rotation to wheel rotations.
    Computes the angular displacement of the left and right wheels
    in order to rotate a rigid body by the given degrees with a
    turning radius of 0.
    Return value is (left, right) in degrees.
    """
    # The exact ratio depends on whether the motor is
    # spinning in its forward or backward direction
    RATIO_F, RATIO_B = (4269.9 / 360.0), (4042.075 / 360.0)

    # Multiply by ratio between one body angle unit and one wheel angle unit
    if bodyAngle >= 0:
        return (-bodyAngle * RATIO_B), (bodyAngle * RATIO_F)
    else:
        return (-bodyAngle * RATIO_F), (bodyAngle * RATIO_B)

def computeWheelAnglesForForward(forwardDistanceInches: float) -> tuple[float, float]:
    """
    Effectively converts a body translation to wheel rotations.
    Computes the angular displacement of the left and right wheels
    in order to drive a rigid body the given number of inches.
    Return value is (left, right) in degrees.
    """
    wheelAngle = forwardDistanceInches * 49.822 # deg/in
    return wheelAngle, wheelAngle

def computeDeltaThetaDeg(previousAngle: float, currentAngle: float) -> float:
    dTheta = currentAngle - previousAngle
    if abs(dTheta) > 180.0:
        if currentAngle > previousAngle:
            dTheta = currentAngle - (360.0 + previousAngle)
        else:
            dTheta = currentAngle + (360.0 - previousAngle)
    # Divide by 2, the motor-sproket gear ratio
    return dTheta / 2.0

if __name__ == "__main__":
    turnAngle = 90.0
    angleL, angleR = computeWheelAnglesForTurn(turnAngle)
    print(f"{turnAngle:3f}°: L{angleL:3f}°, R{angleR:3f}°")

    forwardDistance = 12.0
    angleL, angleR = computeWheelAnglesForForward(forwardDistance)
    print(f"{forwardDistance:3f}\": L{angleL:3f}°, R{angleR:3f}°")

    forwardDistance = -12.0
    angleL, angleR = computeWheelAnglesForForward(forwardDistance)
    print(f"{forwardDistance:3f}\": L{angleL:3f}°, R{angleR:3f}°")

