from svgpathtools import Path
from numpy import arange
from typing import Tuple
import sys

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