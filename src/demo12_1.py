from svgpathtools import parse_path
from nav_utils import RigidBodyState
from path_following import follow_path, trackDisplacement

if __name__ == "__main__":
    path = parse_path("M 0 0 L 24 0 L 0 0")

    robotState = RigidBodyState(complex(0, 0), 0)

    trackDisplacement(-1, 1)
    exit()

    follow_path(robotState, path, None)

    print("Path done!")
