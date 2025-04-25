from threading import Thread
from typing import Union
import numpy as np
from rplidar import RPLidar
from time import sleep

PORT_NAME = '/dev/ttyUSB0'
lidar: RPLidar
_rawScanData: dict[float, float] = {}
_scanData: dict[float, float] = None

class LidarScanData:
    _data: dict[float, float]

    def __init__(self, data: dict[float, float]):
        self._data = data

    def _bisect(self, index: float) -> float:
        if index < 0 or index >= 360:
            raise IndexError

        best_diff = float("inf")
        best_key: float

        for k in self._data:
            new_diff = abs(index - k)
            if new_diff < best_diff:
                best_diff = new_diff
                best_key = k
        
        return best_key

    def __getitem__(self, index: Union[slice, float]):
        # Check for simple case
        if not isinstance(index, slice):
            splitIndex = self._bisect(index)
            return self._data[splitIndex]
        
        # Gonna slice, need to sort dictionary
        slicedDict: dict[float, float] = {}
        for k, v in self._data.items():
            if k >= index.start and k < index.stop:
                slicedDict[k] = v
        return LidarScanData(slicedDict)
    
    def __setitem__(self, index: float, value: float):
        self._data.__setitem__(index, value)
    
    def __delitem__(self, index: float, value: float):
        splitIndex = self._bisect(index)
        self._data.__delitem__(splitIndex, value)

    def __iter__(self):
        for elem in self._data.items():
            yield elem

    def __repr__(self):
        return self._data.__repr__()

    def __str__(self):
        return self._data.__str__()

    def data(self) -> dict[float, float]:
        return self._data

def _scanLoop():
    global _scanData
    global _rawScanData

    for (new_scan, quality, angle, distance) in lidar.iter_measures(scan_type='express'):
        if new_scan:
            _scanData = dict(_rawScanData)
            _rawScanData.clear()
        if distance != 0.0:
            # Un-mirror the image, align with x-y axes, then correct orientation
            angle = np.mod(360 - angle + 11.4 + 90.0, 360.0)
            # Convert mm to in
            _rawScanData[angle] = distance * 0.03937008

def scan() -> LidarScanData:
    # Wait for scan data to become available
    while _scanData == None:
        sleep(0.1)
    return LidarScanData(dict(_scanData))

def cleanScan() -> LidarScanData:
    """
    Cleans a raw scan and returns data in inches
    """
    data = scan()
    filteredData: dict[float, float] = {}
    for angle, dist in data:
        # Ignore distances less than ~0.5 in
        if dist >= 0.5:
            filteredData[angle] = dist
    return LidarScanData(filteredData)

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
                if sum(data.data().values()) > 0:
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

def disconnect():
    global lidar
    lidar.stop_motor()
    lidar.stop()
    lidar.disconnect()

def _cosDeg(thetaDeg: float) -> float:
    thetaRad = np.deg2rad(thetaDeg)
    return float(np.cos(thetaRad))

def getMinimumDistances() -> list[float]:
    global _box
    if _box != None:
        return _box

    # Creating the "Box of View"
    _box = []
    for x in range(0, 180):
        value = minimumDistance(x)
        _box.append(value)
    
    return _box

def minimumDistance(angle: float) -> float:
    x = np.mod(angle, 360.0)
    
    if x < 59:
        return 15 / _cosDeg(x)
    if x < 90:
        return 24 / (_cosDeg(90-x))
    if x < 123:
        return 24 / (_cosDeg(x-90))
    if x < 180:
        return 15 / (_cosDeg(180-x))
    return 0.0

if __name__ == "__main__":
    if False:
        init()
        with open("logs/lidar.csv", 'w') as f:
            lines = [f"{a},{d}\r\n" for a, d in cleanScan()]
            f.writelines(lines)
        disconnect()
    else:
        import numpy as np
        import matplotlib.pyplot as plt

        data: dict[float, float] = {}
        with open("logs\\lidar.csv", 'r') as f:
            for line in f.readlines():
                t, d = line.split(',')
                t, d = float(t), float(d)
                data[t] = d

        thetas = list([np.deg2rad(t) for t in data.keys()])
        distances = list(data.values())
        min_distances = [minimumDistance(t) for t in data.keys()]
        data = LidarScanData(data)
        
        print(f"Near wall: {data[0]}")
        print(f"Far wall: {data[270]}")

        fig = plt.figure()
        ax = fig.add_subplot(projection='polar')
        c = ax.scatter(thetas, distances)
        ax.scatter(thetas, min_distances)
        plt.show()
