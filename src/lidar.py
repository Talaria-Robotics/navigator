from adafruit_rplidar import RPLidar
from math import floor
from sys import float_info

PORT_NAME = '/dev/ttyUSB0'
lidar = RPLidar(None, PORT_NAME, timeout=3)

scan_data = [0] * 360

def testPrint(data):
    angles_of_interest = [0, 90, 180, 270]
    for angle in angles_of_interest:
        dist = data[angle]
        print(f"{angle}°: {dist}")
    
    nearest_angle = 0
    nearest_dist = float_info.max
    for angle, dist in zip(range(len(data)), data):
        if dist < nearest_dist:
            nearest_dist = dist
            nearest_angle = angle
    print(f"Nearest: {nearest_angle}°, {nearest_dist}")
    print()

def scan() -> list[float]:
    lidar.clear_input()
    for scan in lidar.iter_scans():
        for (quality, angle, distance) in scan:
            clampedAngle = min([359, round(angle)])
            scan_data[clampedAngle] = distance
    
        # Return early, we just care about the current iteration
        return scan_data

def disconnect():
    lidar.stop()
    lidar.disconnect()