from threading import Thread
from typing import Union
from numpy import mod
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
            # Convert mm to in
            _rawScanData[angle] = distance * 0.0393700787

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
    scopedData: LidarScanData = data[90:270]
    filteredData: dict[float, float] = {}
    for angle, dist in scopedData:
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
            pass

def disconnect():
    global lidar
    lidar.stop_motor()
    lidar.stop()
    lidar.disconnect()

if __name__ == "__main__":
    init()
    while (1):
        data = cleanScan()._data
        angles, distances = list(data.keys()), list(data.values())
        #print(list(zip(angles, distances)))

        if len(distances) > 0:
            min_dist = min(distances)
            print(angles[distances.index(min_dist)], min_dist)
        print("----")


