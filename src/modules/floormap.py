from svgpathtools import parse_path

class FloorMap:
    def parse(self, filePath: str) -> None:
        floormap_lines = []
        with open(filePath, "r") as file:
            floormap_lines = file.readlines()
        
        paths = []
        for line in floormap_lines:
            path = parse_path(line)
            paths.append(path)
            print(path)


if __name__ == "__main__":
    floormap = FloorMap()
    floormap.parse(r".\maps\TestA.floormap")
