from lidar import LidarScanData, cleanScan, disconnect, init
import numpy as np
from typing import Iterator, Union

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

def nearestWithinBox(scanData: Union[LidarScanData, None] = None) -> Iterator[tuple[float, float]]:
    """
    Returns the angle and distance of all obstacle within the box window.
    """
    if scanData == None:
        scanData = cleanScan()

    for angle, measured in scanData:
        minimum = minimumDistance(angle)
        if measured <= minimum:
            yield angle, measured


if __name__ == "__main__":
    init()
    try:
        while True:
            data = cleanScan()
            nearest = dict(nearestWithinBox(data))
            a = min(nearest, key=nearest.get)
            r = nearest[a]
            print(f"Obstacle at {a:.1f}° {r:.2f}\"")
    except KeyboardInterrupt:
        disconnect()