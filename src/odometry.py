import numpy as np

from nav_utils import Pose, normalizeHeading
from vector import polar2cart, rotationMatrix

# define robot geometry
# Tread height = 2 5/16"
# Wheelbase width = 23 1/8"
R = 1.15625                           # wheel radius
L = 11.5625                           # half of the wheelbase

# Calibrated parameters
REVERSE_MULT = 4269.9 / 4042.075      # motors need a bit more when driving backwards
TURN_RATIO_F = 4042.075 / 360.0       # wheel_deg / body_deg
TURN_RATIO_B = 4269.900 / 360.0   
ANGLE_DISTANCE_RATIO = 49.822         # deg/in
DISTANCE_ANGLE_RATIO = 1 / ANGLE_DISTANCE_RATIO         # in/deg

def computeWheelAnglesForTurn(bodyAngle: float) -> tuple[float, float]:
    """
    Effectively converts a body rotation to wheel rotations.
    Computes the angular displacement of the left and right wheels
    in order to rotate a rigid body by the given degrees with a
    turning radius of 0.
    Return value is (left, right) in degrees.
    """
    # Multiply by ratio between one body angle unit and one wheel
    # angle unit. The exact value of this ratio depends on whether
    # the motor is being driven forward or backward.

    if bodyAngle >= 0:
        return (-bodyAngle * TURN_RATIO_B), (bodyAngle * TURN_RATIO_F)
    else:
        return (-bodyAngle * TURN_RATIO_F), (bodyAngle * TURN_RATIO_B)

def computeWheelAnglesForForward(forwardDistanceInches: float) -> tuple[float, float]:
    """
    Effectively converts a body translation to wheel rotations.
    Computes the angular displacement of the left and right wheels
    in order to drive a rigid body the given number of inches.
    Return value is (left, right) in degrees.
    """
    wheelAngle = forwardDistanceInches * ANGLE_DISTANCE_RATIO
    if wheelAngle < 0:
        wheelAngle *= REVERSE_MULT
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

def computePoseFromWheelAngles(startPose: Pose, wheelAngleL: float, wheelAngleR: float):
    distanceL, distanceR = wheelAngleL * DISTANCE_ANGLE_RATIO, wheelAngleR * DISTANCE_ANGLE_RATIO
    if distanceL < 0:
        distanceL /= REVERSE_MULT
    if distanceR < 0:
        distanceR /= REVERSE_MULT

    # Approx. pure forward motion (~½" tolerance)
    if abs(distanceL - distanceR) < (ANGLE_DISTANCE_RATIO / 2):
        posDelta = polar2cart(distanceL, startPose.dir)
        return Pose(startPose.pos + posDelta, startPose.dir)
    
    # Approx. pure rotational motion (~10° body rotation tolerance)
    if np.sign(distanceL) != np.sign(distanceR) \
        and abs(abs(distanceL) - abs(distanceR)) < (10 / TURN_RATIO_F):
        W = 2.0 * L
        headingChangeRad = (distanceR - distanceL) / W
        return Pose(startPose.pos, startPose.dir + np.rad2deg(headingChangeRad))

    raise NotImplementedError(f"Generalized movements not supported\r\n\tStart pose: {startPose}\r\n\tDisp.: {wheelAngleL:.1f}°, {wheelAngleR:.1f}°")

if __name__ == "__main__":
    print("1: Compute angular displacements for target")
    print("2: Update pose from angular displacements")
    selection = input("? ")

    if selection == "1":
        turnAngle = 90.0
        angleL, angleR = computeWheelAnglesForTurn(turnAngle)
        print(f"{turnAngle:3f}°: L{angleL:3f}°, R{angleR:3f}°")

        forwardDistance = 12.0
        angleL, angleR = computeWheelAnglesForForward(forwardDistance)
        print(f"{forwardDistance:3f}\": L{angleL:3f}°, R{angleR:3f}°")

        forwardDistance = -12.0
        angleL, angleR = computeWheelAnglesForForward(forwardDistance)
        print(f"{forwardDistance:3f}\": L{angleL:3f}°, R{angleR:3f}°")
    elif selection == "2":
        #forwardDistance = 12.0
        #angleL, angleR = computeWheelAnglesForForward(forwardDistance)
        #newPose = computePoseFromWheelAngles(Pose(), angleL, angleR)
        #rint(newPose)

        angleL, angleR = -2149.6, 2067.6
        newPose = computePoseFromWheelAngles(Pose(), angleL, angleR)
        print(newPose)
