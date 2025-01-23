from svgpathtools import parse_path, disvg, Path
from numpy import arange
from typing import Tuple
import sys

def _closestPointOnPath(path: Path, point: complex) -> Tuple[float, complex]:
    closest = None
    smallestDistance = sys.float_info.max

    for t in arange(0, 1, 0.01):
        pathPoint: complex = path.point(t)
        distance = abs(pathPoint - point)
        if distance < smallestDistance:
            smallestDistance = distance
            closest = (float(t), pathPoint)
        
    return closest

class FloorMap:
    def __init__(self, filePath: str):
        floormapLines = []
        with open(filePath, "r") as file:
            floormapLines = file.readlines()
        
        paths = []
        for line in floormapLines:
            path = parse_path(line)
            paths.append(path)
        
        closeest = _closestPointOnPath(paths[0], complex(5, 5))
        print(closeest)


if __name__ == "__main__":
    floormap = FloorMap(r".\maps\TestA.floormap")
