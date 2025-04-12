from collections.abc import Generator
from svgpathtools import Path
from numpy import arange
from typing import  Tuple
import sys
import numpy as np

class RigidBodyState:
    pos: complex = complex(0)
    """The position of the body's center of mass."""

    dir: float = 0.0
    """The heading angle in degrees relative to the forward direction of the body."""

    def __init__(self, pos: complex = complex(0), dir: float = 0.0):
        self.pos = pos
        self.dir = dir

    def __str__(self) -> str:
        return f"{self.pos.real:.2f}\", {self.pos.imag:.2f}\", {self.dir:.1f}°"
    
    def __add__(self, other):
        pos = self.pos + other.pos
        dir = self._addDir(other.dir)
        return RigidBodyState(pos, dir)
    
    def __sub__(self, other):
        pos = self.pos - other.pos
        dir = self._addDir(-other.dir)
        return RigidBodyState(pos, dir)
    
    def _addDir(self, otherDir: float):
        return addAnglesDeg(self.dir, otherDir)

def addAnglesDeg(theta1: float, theta2: float) -> float:
    theta3 = theta1 + theta2
    return np.fmod(theta3, 360.0)


def bboxCombine(bboxes: list[Tuple[float, float, float, float]]) -> Tuple[float, float, float, float]:
    xmin, xmax, ymin, ymax = sys.float_info.max, sys.float_info.min, sys.float_info.max, sys.float_info.min
    for bbox in bboxes:
        if bbox[0] < xmin:
            xmin = bbox[0]
        if bbox[1] > xmax:
            xmax = bbox[1]
        if bbox[2] < ymin:
            ymin = bbox[2]
        if bbox[3] > ymax:
            ymax = bbox[3]
    return xmin, xmax, ymin, ymax

def closestPointOnPath(path: Path, point: complex) -> Tuple[float, complex]:
    closest = (-1.0, None, sys.float_info.max)
    epsilon = 0.0001
    step = 0.01

    while True:
        current = _closestPointOnPath(path, point, step)
        delta = abs(current[2] - closest[2])
        print(delta)
        if delta > 0:
            closest = current
        if delta > epsilon:
            step /= 10
        else:
            break
        
    return closest

def _closestPointOnPath(path: Path, point: complex, step: float) -> Tuple[float, complex, float]:
    closest = (-1.0, None, sys.float_info.max)

    for t in arange(0, 1, step):
        pathPoint: complex = path.point(t)
        distance = abs(pathPoint - point)
        if distance < closest[2]:
            closest = (float(t), pathPoint, distance)
        
    return closest

def discretizePath(path: Path) -> list[RigidBodyState]:
    # Preston doesn't need hundredth-of-an-inch accuracy,
    # so any two points with a change in heading of less than
    # 0.04774 degrees is assumed to be a straight line.
    # This value was computed as the maximum angle that
    # produces less than 1/100" across a distance of 10 feet.
    MERGE_TOLERANCE_DIR = 0.04774
    MERGE_TOLERANCE_POS = 6

    # Determine delta t to achieve segments of <1 inch
    dt = path.ilength(1.0)

    points: list[RigidBodyState] = []
    lastState: RigidBodyState = None

    for t in np.arange(0.0, 1.0 + dt, dt):
        if t > 1.0:
            break

        # Use t-value to get position and orientation
        baseVec = path.point(t)
        tangentVec = path.unit_tangent(t)

        # Note that the heading is in degrees, relative to +x
        heading = np.angle(tangentVec, deg=True)
        
        state = RigidBodyState()
        state.pos = baseVec
        state.dir = heading

        # For straight lines, there's no need to go a single inch
        # at a time, so let's combine it with the previous one
        if lastState != None \
            and abs(lastState.dir - heading) <= MERGE_TOLERANCE_DIR \
            and abs(lastState.pos - baseVec) <= MERGE_TOLERANCE_POS:
            # Skip previous state
            points[-1] = state

            # Make sure we don't duplicate this state or update the
            # previous heading. This should help prevent long, gentle
            # curves from being optimized to straight lines
            continue

        points.append(state)
        lastState = state
    
    return points

if __name__ == "__main__":
    from svgpathtools import parse_path

    path = parse_path("M 0 0 L 24 0 L 0 0")

    robotState = RigidBodyState(complex(0, 0), 0)

    for point in discretizePath(path):
        correction = point - robotState
        robotState += correction
        print(correction)
