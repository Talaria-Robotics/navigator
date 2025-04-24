from lidar import LidarScanData, cleanScan, disconnect, init
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
    for x in range(0, 180):
        value = minimumDistance(x)
        _box.append(value)
    
    return _box

def minimumDistance(angle: float) -> float:
    x = np.mod(angle, 360.0)
    
    if x < 59:
        return 15 / _cosDeg(x)
    if x < 90:
        return 24 / (_cosDeg(90-x))
    if x < 123:
        return 24 / (_cosDeg(x-90))
    if x < 180:
        return 15 / (_cosDeg(180-x))
    return 0.0

def nearestWithinBox(scanData: Union[LidarScanData, None] = None) -> Union[tuple[int, float], None]:
    """
    Returns the angle and distance of the nearest obstacle within
    the box window, or None if no obstacle was within the box.
    """
    if scanData == None:
        scanData = cleanScan()

    for angle, measured in scanData:
        minimum = minimumDistance(angle)
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