from threading import Thread
from rplidar import RPLidar
from sys import float_info

PORT_NAME = '/dev/ttyUSB0'
lidar = RPLidar(PORT_NAME)
_scanData = [0] * 360

def _scanLoop():
    for scan in lidar.iter_scans():
        for (quality, angle, distance) in scan:
            clampedAngle = min([359, round(angle)])
            _scanData[clampedAngle] = distance

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
    return _scanData
    
def init():
    # The A1 LIDAR really doesn't like one-shot measurements,
    # so all readings have to be taking continuously in the same loop.
    # If we tried that in the scan() method, we'd get stuck in an
    # infinite loop and hang the caller. Instead, we'll spin up
    # a separate thread that updates _scanData as readings come in.
    _scanThread = Thread(target=_scanLoop, daemon=True)
    _scanThread.start()

def disconnect():
    lidar.stop_motor()
    lidar.stop()
    lidar.disconnect()


if __name__ == "__main__":
    from time import sleep

    init()
    while True:
        print(scan())
        sleep(1.0)
