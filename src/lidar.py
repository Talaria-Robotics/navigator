from collections.abc import Generator
from threading import Thread
from typing import Union
from rplidar import RPLidar
from sys import float_info
from operator import itemgetter
from time import sleep

PORT_NAME = '/dev/ttyUSB0'
lidar: RPLidar
_scanData = None

def _scanLoop():
    global _scanData
    if _scanData == None:
        _scanData = [0] * 360

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

def scan() -> Union[list[float], None]:
    # Wait for scan data to become available
    while _scanData == None:
        sleep(0.1)
    return _scanData

def cleanScan() -> Generator[float]:
    """
    Cleans a raw scan and returns data in inches
    """
    data = scan()
    for angle, dist in enumerate(data):
        if angle < 90 or angle > 270:
            continue

        # Ignore distances less than ~16 mm
        if dist < 16.0:
            yield 0.0
        else:
            # Convert mm to in
            yield dist * 0.0393700787

def getNearest() -> tuple[float, float]:
    data = cleanScan()
    angle, dist = min(enumerate(data), key=itemgetter(1))
    return dist, angle

def testCalibrate():
    data = scan()
    n = 10
    for i in range(0, len(data), n):
        startAngle = i
        endAngle = i + n
        dataChunk = data[i:i + n]
        averageDistance = sum(dataChunk) / n
        print(f"[{startAngle}, {endAngle}): {averageDistance:.2f}")
    
def init():
    global lidar
    # The A1 LIDAR has lots of issues connecting. We'll just keep
    # retrying unitl it works.
    while True:
        try:
            lidar = RPLidar(PORT_NAME)
    
            # The A1 LIDAR really doesn't like one-shot measurements,
            # so all readings have to be taking continuously in the same loop.
            # If we tried that in the scan() method, we'd get stuck in an
            # infinite loop and hang the caller. Instead, we'll spin up
            # a separate thread that updates _scanData as readings come in.
            _scanThread = Thread(target=_scanLoop, daemon=True)
            _scanThread.start()

            # Wait for LIDAR to actually start retuning data
            print("Waiting for LIDAR to be ready...")
            while True:
                data = scan()
                if sum(data) > 0:
                    break
                sleep(0.5)

            print("LIDAR initialized")
            break
        except KeyboardInterrupt:
            disconnect()
            raise
        except:
            print("Failed to initialize LIDAR, retrying...")
            disconnect()
            sleep(0.5)
            pass

def disconnect():
    global lidar
    lidar.stop_motor()
    lidar.stop()
    lidar.disconnect()


if __name__ == "__main__":
    from time import sleep

    init()
    try:
        testCalibrate()
    except KeyboardInterrupt:
        disconnect()
