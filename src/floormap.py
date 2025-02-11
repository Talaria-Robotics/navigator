from svgpathtools import parse_path, Path
from nav_utils import bboxCombine
from itertools import combinations
import itertools

from pathfinding.core.graph import Graph
from pathfinding.finder.dijkstra import DijkstraFinder

class FloorMap:
    def __init__(self, filePath: str):
        SECTION_META = "[Meta]"
        SECTION_ROOMS = "[Rooms]"
        SECTION_NODES = "[Nodes]"
        SECTION_PATHS = "[Paths]"

        self.name: str = None
        self.id: str = None
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
    
    def planTrip(self, stopIds: list[str]) -> list[str]:
        # Build graph
        edges: list[list[any, any, float]] = []
        for pathPoints, path in self.paths.items():
            pathStartId, pathEndId = pathPoints
            pathLength = path.length()
            edges.append([pathStartId, pathEndId, pathLength])
        
        # Compute the shortest path between each pair of stops
        shortestPaths = {}
        for startNodeId, endNodeId in combinations(stopIds, 2):
            graph = Graph(edges=edges, bi_directional=True)
            finder = DijkstraFinder()
            shortPath, shortPathLength = finder.find_path(graph.node(startNodeId), graph.node(endNodeId), graph)
            shortPathIds = [node.node_id for node in shortPath]

            shortestPaths[(startNodeId, endNodeId)] = (shortPathLength, shortPathIds)
            shortestPaths[(endNodeId, startNodeId)] = (shortPathLength, shortPathIds[::-1])

            # The pathfinding library is dumb and modifies the edges list
            for edge in edges:
                edge[0] = edge[0].node_id
                edge[1] = edge[1].node_id
        
        homeId = stopIds[0]
        shortestPath: list[str] = None
        shortestPathLength = float("inf")
        for x in itertools.permutations(stopIds[1:]):
            candidatePath = [homeId, *x, homeId]
            
            candidateFullPath = []
            candidateLength = 0
            for i in range(len(candidatePath) - 1):
                startNodeId = candidatePath[i]
                endNodeId = candidatePath[i + 1]
                subpathLength, subpath = shortestPaths[(startNodeId, endNodeId)]
                candidateLength += subpathLength
                candidateFullPath += subpath[:-1]
            candidateFullPath.append(homeId)

            if candidateLength < shortestPathLength:
                shortestPath = candidateFullPath
                shortestPathLength = candidateLength
        return shortestPath

    def toSvg(self):
        xmin, xmax, ymin, ymax = bboxCombine([p.bbox() for p in self.paths.values()])

        scaleFactor = 1000 / max(xmax, ymax)
        vbWidth = 2 * xmax * scaleFactor
        vbHeight = 2 * ymax * scaleFactor

        svgStr = f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{vbWidth}\" height=\"{vbHeight}\" >"
        
        svgStr += f"<g transform=\"scale({scaleFactor})\">"
        
        for pathId, path in self.paths.items():
            svgStr += f"<path id=\"{pathId}\" d=\"{path.d()}\" stroke-width=\"2\" stroke=\"#C83737\" fill=\"transparent\" />"
        
        for nodeId, nodePoint in self.nodes.items():
            nodeColor = "#500000"
            if nodeId in self.rooms.keys():
                nodeColor = "#005000"
            svgStr += f"<circle id=\"{nodeId}\" cx=\"{nodePoint.real}\" cy=\"{nodePoint.imag}\" r=\"2\" fill=\"{nodeColor}\"/>"
        
        svgStr += "</g></svg>"
        return svgStr


if __name__ == "__main__":
    from pathlib import Path 

    floormapPath = Path(".", "maps", "FermierHall_Small.floormap")
    floormap = FloorMap(str(floormapPath))

    floormapSvgPath = floormapPath.with_suffix(".svg")
    with floormapSvgPath.open("w") as file:
        floormapSvg = floormap.toSvg()
        file.write(floormapSvg)

    trip = floormap.planTrip(["r111a", "r106-1"])
    print(trip)
