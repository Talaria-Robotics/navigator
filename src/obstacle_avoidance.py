from lidar import cleanScan, disconnect, init
import numpy as np
from typing import Union

_box = None

def _cosDeg(thetaDeg: float) -> float:
    thetaRad = np.deg2rad(thetaDeg)
    return float(np.cos(thetaRad))

def getMinimumDistances() -> list[float]:
    global _box
    if _box != None:
        return _box

    # Creating the "Box of View"
    _box = []
    for x in range(0, 59):
        value = 15 / _cosDeg(x)
        _box.append(value)
    for x in range(59, 90):
        value = 24 / (_cosDeg(90-x))
        _box.append(value)

    for x in range(90, 123):
        value = 24 / (_cosDeg(x-90))
        _box.append(value)
    for x in range(123, 180):
        value = 15 / (_cosDeg(180-x))
        _box.append(value)
    
    return _box

def nearestWithinBox(scanData: Union[list[float], None] = None) -> Union[tuple[int, float], None]:
    """
    Returns the angle and distance of the nearest obstacle within
    the box window, or None if no obstacle was within the box.
    """
    if scanData == None:
        scanData = list(cleanScan())

    minDistances = getMinimumDistances()
    for angle in range(0, 180):
        measured = scanData[angle]
        minimum = minDistances[angle]
        if measured <= minimum:
            return angle, measured
    return None


if __name__ == "__main__":
    init()
    try:
        while True:
            nearest = nearestWithinBox()
            if nearest != None:
                a, r = nearest
                print(f"Obstacle at {r:.2f}\", {a:.1f}°")
    except KeyboardInterrupt:
        disconnect()