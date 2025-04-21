import numpy as np
from typing import Union

def _cosDeg(thetaDeg: float) -> float:
    thetaRad = np.deg2rad(thetaDeg)
    return float(np.cos(thetaRad))

def getMinimumDistances() -> list[float]:
    # Creating the "Box of View"
    box = []
    for x in range(0, 59):
        value = 15 / _cosDeg(x)
        box.append(value)
    for x in range(59, 90):
        value = 24 / (_cosDeg(90-x))
        box.append(value)

    box.append(24)

    for x in range(91, 148):
        value = 24 / (_cosDeg(x-90))
        box.append(value)
    for x in range(148, 180):
        value = 15 / (_cosDeg(180-x))
        box.append(value)
    
    return box

def nearestWithinBox(scanData: list[float]) -> Union[tuple[int, float], None]:
    """
    Returns the angle and distance of the nearest obstacle within
    the box window, or None if no obstacle was within the box.
    """
    minDistances = getMinimumDistances()
    for angle in range(0, 180):
        measured = scanData[angle]
        minimum = minDistances[angle]
        if measured <= minimum:
            return angle, measured
    return None


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    r = getMinimumDistances()
    theta = list(range(0, 180))
    for a in theta:
        theta[a] = np.deg2rad(a)
    
    plt.polar(theta, r)
    plt.show()