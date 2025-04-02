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

    # Use t-value to get position and orientation
    targetLocation = path.point(1.0)
    targetHeading = np.angle(targetLocation, deg=True)

    # Note that the heading is in degrees, relative to +x
    targetState = RigidBodyState()
    targetState.pos = targetLocation
    targetState.dir = targetHeading
    
    correction = targetState - botState

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
    angDispSignL, angDispSignR = np.sign(targetAngDispL), np.sign(targetAngDispR)
    motorSpeedL, motorSpeedR = 0.8 * angDispSignL, 0.8 * angDispSignR
    
    doneL, doneR = False, False
    angDispL, angDispR = 0, 0
    
    lastAngleL, lastAngleR = readShaftPositions()
    lastTargetDeltaL, lastTargetDeltaR = None, None

    dataEntries = []

    try:
        print("Entering step loop...")
        while not (doneL and doneR):
            angleL, angleR = readShaftPositions()
            
            # Handle when angle overflows (crossing 0 deg)
            dThetaL = computeDeltaThetaDeg(lastAngleL, angleL)
            angDispL += dThetaL

            dThetaR = computeDeltaThetaDeg(lastAngleR, angleR)
            angDispR += dThetaR

            lastAngleL, lastAngleR = angleL, angleR

            # Compute the remaining angular displacement
            targetDeltaL, targetDeltaR = targetAngDispL - angDispL, targetAngDispR - angDispR
            print(f"Disp remaining: {targetDeltaL:.1f} {targetDeltaR:.1f}")

            # If the last remaining displacement has a different sign than the
            # the current remaining displacement, then by the intermediate value theorem
            # we must have passed zero remaining displacement
            if lastTargetDeltaL != None and np.sign(lastTargetDeltaL) != np.sign(targetDeltaL):
                doneL = True
                driveLeft(0)
            else:
                driveLeft(motorSpeedL)

            if lastTargetDeltaR != None and np.sign(lastTargetDeltaR) != np.sign(targetDeltaR):
                doneR = True
                driveRight(0)
            else:
                driveRight(motorSpeedR)

            lastTargetDeltaL, lastTargetDeltaR = targetDeltaL, targetDeltaR

            # Ensure the delta theta is greater than the error
            # in the encoder measurements
            sleep(0.05)

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
