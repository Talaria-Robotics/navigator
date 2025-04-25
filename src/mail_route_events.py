from models import *
from typing import Optional

class MailRouteEvent(Serializable):
    disc: str
    orderNumber: int

    def __init__(self, disc: str, orderNumber: Optional[int] = None) -> None:
        self.disc = disc
        if orderNumber:
            self.orderNumber = orderNumber

class ArrivedAtStopEvent(MailRouteEvent):
    room: MailRouteRoom
    bin: MailBin

    def __init__(self, room: MailRouteRoom, bin: MailBin) -> None:
        self.room = room
        self.bin = bin
        super().__init__("ArrivedAtStop")

class InTransitEvent(MailRouteEvent):
    room: MailRouteRoom

    def __init__(self, room: MailRouteRoom) -> None:
        self.room = room
        super().__init__("InTransit")

class ReturnHomeEvent(MailRouteEvent):
    def __init__(self) -> None:
        super().__init__("ReturnHome")

class DoneEvent(MailRouteEvent):
    def __init__(self) -> None:
        super().__init__("Done")