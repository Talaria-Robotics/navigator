from svgpathtools import parse_path, disvg, Path
from nav_utils import closestPointOnPath

class FloorMap:
    def __init__(self, filePath: str):
        SECTION_META = "[Meta]"
        SECTION_BINS = "[Bins]"
        SECTION_NODES = "[Nodes]"
        SECTION_PATHS = "[Paths]"

        self.name: str = None
        self.id: str = None
        self.bins: dict[int, str] = {}
        self.nodes: dict[str, complex] = {}
        self.paths: dict[tuple[str, str], Path] = {}

        with open(filePath, "r") as file:
            currentSection = None
            for line in file.readlines():
                line = line.strip()
                if len(line) <= 0:
                    continue

                if line.startswith('['):
                    currentSection = line
                    continue

                if currentSection == SECTION_META:
                    if self.name == None:
                        self.name = line
                    else:
                        self.id = line
                elif currentSection == SECTION_BINS:
                    binNum, binName = line.split(':')
                    binNum = int(binNum)
                    binName = binName.strip()
                    self.bins[binNum] = binName
                elif currentSection == SECTION_NODES:
                    nodeId, nodeCoords = line.split(':')
                    nodeId = nodeId.strip()
                    nodeX, nodeY = [float(c) for c in nodeCoords.split(',')]
                    self.nodes[nodeId] = complex(nodeX, nodeY)
                elif currentSection == SECTION_PATHS:
                    pathConnection, pathSvg = line.split(':')
                    pathStartId, pathEndId = [c.strip() for c in pathConnection.split('>')]
                    pathStart = self.nodes[pathStartId]
                    pathEnd = self.nodes[pathEndId]
                    pathSvg = f"M {pathStart.real} {pathStart.imag} {pathSvg.strip()} L {pathEnd.real} {pathEnd.imag}"
                    self.paths[(pathStartId, pathEndId)] = parse_path(pathSvg)
        
        print("NODES")
        print(self.nodes)
        print()
        print("PATHS")
        print(self.paths)
        for path in self.paths.values():
            disvg(path)


if __name__ == "__main__":
    floormap = FloorMap(r".\maps\TestA.floormap")
