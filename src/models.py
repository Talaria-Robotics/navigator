from typing import Dict, List, Union, Optional
import json

class Serializable:
    def toJSON(self):
        return self.__dict__

class Identified(Serializable):
    id: str
    name: str

    def __init__(self, id: Optional[str] = None, name: Optional[str] = None) -> None:
        if id:
            self.id = id
        if name:
            self.name = name

class MailRouteRoom(Identified):
    def __init__(self, id: Optional[str] = None, name: Optional[str] = None) -> None:
        super().__init__(id, name)

class MailBin(Serializable):
    number: int
    name: str

    def __init__(self, number: Optional[int] = None, name: Optional[str] = None) -> None:
        if number:
            self.number = number
        if name:
            self.name = name

class PossibleMailRouteInfo(Identified):
    rooms: List[MailRouteRoom]
    bins: List[MailBin]

class MailRouteStop(Serializable):
    roomId: str
    binNumber: int

class RequestedMailRoute(Serializable):
    stops: Dict[int, str]

    def __init__(self, json: dict[str, str]) -> None:
        self.stops = {}
        for k, v in json.items():
            self.stops[int(k)] = str(v)