from svgpathtools import parse_path
from nav_utils import Pose
from path_following import follow_path, trackDisplacement

if __name__ == "__main__":
    path = parse_path("M 0 0 L 24 0 L 0 0")

    robotState = Pose(complex(0, 0), 0)

    follow_path(robotState, path, None)

    print("Path done!")
