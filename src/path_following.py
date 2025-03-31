from queue import Queue
from floormap import FloorMap
from mail_route_events import *
from models import *
from svgpathtools import Path
from typing import Callable
from nav_utils import RigidBodyState, discretizePath
from inverse_kinematics import computeWheelAnglesForTurn, computeWheelAnglesForForward, computeDeltaThetaDeg
import data_log as dl
import numpy as np
from time import sleep

MOCK = False

if not MOCK:
    from motor import drive, driveLeft, driveRight
    from encoder import readShaftPositions
else:
    from motor_mock import drive, driveLeft, driveRight, startMock, stopMock
    from encoder_mock import readShaftPositions

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
    botState = RigidBodyState()
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

        botState.pos = floorplan.nodes[currentNodeId]

        pathToFollow: Path = floorplan.getShortestAdjacentPath(currentNodeId, nextNodeId)
        with dl.startLogSession(f"{currentNodeId}_to_{nextNodeId}") as logSession:
            follow_path(botState, pathToFollow, logSession)

def follow_path(botState: RigidBodyState, path: Path,
                logSession: dl.DataLogSession) -> RigidBodyState:
    # Configure data logging
    logSession.writeHeaders(["angleL", "angleR", "angDispL", "angDispR", "dThetaL", "dThetaR"])

    segments = discretizePath(path)
    for targetState in segments:
        correction = targetState - botState

        # TODO: Keep track of how much the wheels rotate,
        # as this is what allows us to compute the actual position.
        # Closed loop control!!!

        # Correct heading
        targetAngDispL, targetAngDispR = computeWheelAnglesForTurn(correction.dir)
        driveToAngularDisplacement(targetAngDispL, targetAngDispR, logSession)

        # Correct forward
        targetAngDispL, targetAngDispR = computeWheelAnglesForForward(abs(correction.pos))
        driveToAngularDisplacement(targetAngDispL, targetAngDispR, logSession)

        botState += correction

    print(f"Navi: {botState}")
    return botState

def driveToAngularDisplacement(targetAngDispL: float, targetAngDispR: float,
                               logSession: dl.DataLogSession):
    targetAngDispL, targetAngDispR = np.rad2deg(targetAngDispL), np.rad2deg(targetAngDispR)
    lastAngleL, lastAngleR = readShaftPositions()
    angDispL, angDispR = 0, 0
    angDispSignL, angDispSignR = np.sign(targetAngDispL), np.sign(targetAngDispR)

    oneRev = 360.0 #2 * np.pi

    try:
        print("Moving motors")
        driveLeft(0.8 * angDispSignL)
        driveRight(0.8 * angDispSignR)
        doneL, doneR = False, False
        dataEntries = []

        print("Entering step loop...")
        while not (doneL and doneR):
            angleL, angleR = readShaftPositions()
            
            # Handle when angle overflows (crossing 0 deg)
            dThetaL = computeDeltaThetaDeg(lastAngleL, angleL) / 2
            angDispL += dThetaL

            dThetaR = computeDeltaThetaDeg(lastAngleR, angleR) / 2
            angDispR += dThetaR

            lastAngleL, lastAngleR = angleL, angleR

            if angDispL >= targetAngDispL:
                doneL = True
                driveLeft(0)
            if angDispR >= targetAngDispR:
                doneR = True
                driveRight(0)

            # Ensure the delta theta is greater than the error
            # in the encoder measurements
            sleep(0.1)

            dataEntries.append([angleL, angleR, angDispL, angDispR, dThetaL, dThetaR])
    except KeyboardInterrupt:
        drive(0)
        print("Navi: Stopping")
        exit()
    
    for entry in dataEntries:
        logSession.writeEntry(entry)

if __name__ == "__main__":
    import os
    from orjson import dumps
    from time import sleep

    with dl.startLogSession(f"plain_test") as logSession:
        correction = RigidBodyState(complex(0, 12), 90.0)

        # Set heading
        targetAngDispL, targetAngDispR = computeWheelAnglesForTurn(correction.dir)
        print(f"Target angular displacement: {targetAngDispL:3f}°, {targetAngDispR:3f}°")
        driveToAngularDisplacement(targetAngDispL, targetAngDispR, logSession)

        # Set forward
        targetAngDispL, targetAngDispR = computeWheelAnglesForForward(abs(correction.pos))
        print(f"Target angular displacement: {targetAngDispL:3f}°, {targetAngDispR:3f}°")
        driveToAngularDisplacement(targetAngDispL, targetAngDispR, logSession)

    exit()

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

    if MOCK:
        startMock()

    transitFeed(route, floorplan, bins, sendEventDebug, waitForConfirmationDebug)
    
    if MOCK:
        stopMock()
