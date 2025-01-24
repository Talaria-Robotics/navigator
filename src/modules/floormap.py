from svgpathtools import parse_path, disvg, Path
from nav_utils import closestPointOnPath

class FloorMap:
    def __init__(self, filePath: str):
        floormapLines = []
        with open(filePath, "r") as file:
            floormapLines = file.readlines()
        
        paths = []
        for line in floormapLines:
            path = parse_path(line)
            paths.append(path)
        
        closeest = closestPointOnPath(paths[0], complex(50, 0))
        print(closeest)


if __name__ == "__main__":
    floormap = FloorMap(r".\maps\TestA.floormap")
