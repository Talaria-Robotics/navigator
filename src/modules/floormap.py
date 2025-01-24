from svgpathtools import parse_path, disvg, Path
from nav_utils import bboxCombine

class FloorMap:
    def __init__(self, filePath: str):
        SECTION_META = "[Meta]"
        SECTION_ROOMS = "[Rooms]"
        SECTION_NODES = "[Nodes]"
        SECTION_PATHS = "[Paths]"

        self.name: str = None
        self.id: str = None
        self.bins: dict[int, str] = {}
        self.rooms: dict[str, str] = {}
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
                elif currentSection == SECTION_ROOMS:
                    roomId, roomName = line.split(':')
                    roomId = roomId.strip()
                    roomName = roomName.strip()
                    self.rooms[roomId] = roomName
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
        
    def toSvg(self):
        xmin, xmax, ymin, ymax = bboxCombine([p.bbox() for p in self.paths.values()])

        scaleFactor = 1000 / max(xmax, ymax)
        vbWidth = 2 * xmax * scaleFactor
        vbHeight = 2 * ymax * scaleFactor

        svgStr = f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{vbWidth}\" height=\"{vbHeight}\" >"
        
        svgStr += f"<g transform=\"scale({scaleFactor})\">"
        
        for pathId, path in self.paths.items():
            svgStr += f"<path id=\"{pathId}\" d=\"{path.d()}\" stroke-width=\"0.25\" stroke=\"#C83737\" fill=\"transparent\" />"
        
        for nodeId, nodePoint in self.nodes.items():
            nodeColor = "#500000"
            if nodeId in self.rooms.keys():
                nodeColor = "#005000"
            svgStr += f"<circle id=\"{nodeId}\" cx=\"{nodePoint.real}\" cy=\"{nodePoint.imag}\" r=\"0.25\" fill=\"{nodeColor}\"/>"
        
        svgStr += "</g></svg>"
        return svgStr


if __name__ == "__main__":
    floormap = FloorMap(r".\maps\TestA.floormap")
    print(floormap.toSvg())
