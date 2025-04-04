from io import TextIOWrapper
import os
import time
from typing import Any, Iterable

_DATA_SEP = ","

class DataLogSession:
    filePath: str | None
    resource: TextIOWrapper | None
    _includeTime: bool
    _startedTimestamp: int | None

    def __init__(self, filePath: str | None, includeTime: bool):
        self.filePath = filePath
        self.resource = None
        self._includeTime = includeTime
        self._startedTimestamp = None

    def writeHeaders(self, headers: Iterable[str]) -> None:
        if not self.resource:
            return

        if self._includeTime:
            headers = ["Time (ms)", *headers]
        self.resource.write(_DATA_SEP.join(headers))
        self.resource.write("\n")

    def writeEntry(self, data: Iterable[Any]) -> None:
        if not self.resource:
            return
        
        if self._includeTime:
            data = [self.time_elapsed(), *data]
        
        dataStrs = [str(d) for d in data]
        self.resource.write(_DATA_SEP.join(dataStrs))
        self.resource.write("\n")

    def time_elapsed(self) -> int:
        return self._time_ms() - self._startedTimestamp

    def _time_ms(self) -> int:
        return time.time_ns() // 1000000

    def __enter__(self):
        if self.filePath:
            # Acquire the resource
            self.resource = open(self.filePath, 'w')
            self._startedTimestamp = self._time_ms()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Release the resource
        if self.resource:
            self.resource.close()
            self.resource = None
            
        self._startedTimestamp = None
        
        return exc_type != None

def startLogSession(name: str, includeTime: bool = True, logDir: str = "logs") -> DataLogSession:
    filePath = os.path.join(logDir, f"{name}.csv")
    return DataLogSession(filePath, includeTime)
