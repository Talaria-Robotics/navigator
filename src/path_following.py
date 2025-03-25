from queue import Queue
from floormap import FloorMap
from mail_route_events import *
from models import *
#from obstacle_avoidance import navigate
from svgpathtools import Path
from typing import Callable


def transitFeed(route: RequestedMailRoute, floorplan: FloorMap, bins: dict[int, str],
                emitEvent: Callable[[MailRouteEvent], None],
                waitForConfirmation: Callable[[], None]):
    print("Preparing route...")
    stopIds = [*route.stops.values()]
    _, tripNodes = floorplan.planTrip(stopIds)
    print(f"Planned route: {tripNodes}")
    
    # The full route is already broken into atoms, which represent
    # the selected path from one node to another node directly
    # connected to it. We'll navigate between these atoms to
    # simplify the navigation logic. 

    # Build a queue to keep track of which stops
    # we've already completed.
    stopQueue = Queue(len(stopIds))
    for stopId in stopIds:
        stopQueue.put(stopId)

    statusesSent: int = 0
    currentPosition: complex
    currentHeading: float
    nextStopId: str | None = stopQueue.get()
    
    for nextNodeIndex in range(1, len(tripNodes)):
        currentNodeId = tripNodes[nextNodeIndex - 1]
        nextNodeId = tripNodes[nextNodeIndex]
        print(f"Navi: {currentNodeId} -> {nextNodeId}")

        if currentNodeId == nextStopId:
            roomName = floorplan.rooms[nextStopId]
            room = MailRouteRoom(nextStopId, roomName)

            # For every bin that has been assigned the current stop,
            # inform the UI we've arrived and wait for the receipient
            # to confirm they've gotten their mail.
            for binNum, roomId in route.stops.items():
                if roomId == nextStopId:
                    binName = bins[binNum]
                    bin = MailBin(binNum, binName)

                    arrivedAtStopEvent = ArrivedAtStopEvent(room, bin)
                    arrivedAtStopEvent.orderNumber = statusesSent
                    
                    #emitEvent(arrivedAtStopEvent)
                    statusesSent += 1

                    #waitForConfirmation()

            if stopQueue.empty():
                nextStopId = None
            else:
                nextStopId = stopQueue.get()
            
                # Let the UI know we're going to a new stop
                roomName = floorplan.rooms[nextStopId]
                room = MailRouteRoom(nextStopId, roomName)
                inTransitEvent = InTransitEvent(room)
                inTransitEvent.orderNumber = statusesSent
                
                #emitEvent(inTransitEvent)
                statusesSent += 1

        currentPosition = floorplan.nodes[currentNodeId]

        pathToFollow: Path = floorplan.getShortestAdjacentPath(currentNodeId, nextNodeId)
        follow_path(pathToFollow)

def follow_path(path: Path) -> tuple[complex, float]:
    # TODO: Break the path into small, linear segments
    pass

if __name__ == "__main__":
    import os
    from orjson import dumps
    from time import sleep

    def sendEventDebug(event: MailRouteEvent):
        eventStr = dumps(event, default=vars)
        print(f"Sending event {eventStr}")

    def waitForConfirmationDebug():
        print("Waiting for confirmation...")

    route = RequestedMailRoute()
    route.stops = {
        1: "room1",
    }

    bins = {
        1: "Letter Slot 1",
        2: "Letter Slot 2",
        3: "Letter Slot 3",
        14: "Package Area",
    }

    floorplan = FloorMap(os.path.join("maps", "PIC_Sample_Map.floormap"))
    print(floorplan.nodes)

    transitFeed(route, floorplan, bins, sendEventDebug, waitForConfirmationDebug)