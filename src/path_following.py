from queue import Queue
from floormap import FloorMap
from mail_route_events import *
from models import *
from svgpathtools import Path
from typing import Callable
from nav_utils import RigidBodyState, discretizePath
from inverse_kinematics import computeWheelAnglesForTurn, computeWheelAnglesForForward, computeDeltaThetaDeg
import data_log as dl
from vector import cart2polar
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
    if logSession:
        logSession.writeHeaders(["angleL", "angleR", "angDispL", "angDispR", "dThetaL", "dThetaR"])

    segments = discretizePath(path)
    for targetState in segments:
        correction = targetState - botState

        # Convert correction to local polar space
        targetDistance, targetStartAngle = cart2polar(correction.pos)
        startAngleCorrection = targetStartAngle - botState.dir

        # Correct initial heading angle
        print(f"Correct heading: {startAngleCorrection:.1f}°")
        targetAngDispL, targetAngDispR = computeWheelAnglesForTurn(startAngleCorrection)
        driveToAngularDisplacement(targetAngDispL, targetAngDispR, logSession)

        # Correct forward distance
        print(f"Correct forward: {targetDistance:.2f}\"")
        targetAngDispL, targetAngDispR = computeWheelAnglesForForward(targetDistance)
        driveToAngularDisplacement(targetAngDispL, targetAngDispR, logSession)

        # TODO: Correct end heading angle
        #targetAngDispL, targetAngDispR = computeWheelAnglesForForward(targetState.dir - targetStartAngle)
        #driveToAngularDisplacement(targetAngDispL, targetAngDispR, logSession)

        # TODO: Verify this
        botState = targetState

    print(f"Bot state: {botState}")
    return botState

def trackDisplacement(angDispSignL, angDispSignR):
    dutyCycle = 0.8
    if angDispSignL != angDispSignR:
        dutyCycle = 1.0

    motorSpeedL, motorSpeedR = dutyCycle * angDispSignL, dutyCycle * angDispSignR
    
    angDispL, angDispR = 0, 0
    lastAngleL, lastAngleR = readShaftPositions()
    lastTargetDeltaL, lastTargetDeltaR = np.nan, np.nan

    try:
        print("Entering step loop...")
        driveRight(motorSpeedL)
        driveLeft(motorSpeedR)
        while True:
            angleL, angleR = readShaftPositions()
            
            # Handle when angle overflows (crossing 0 deg)
            dThetaL = computeDeltaThetaDeg(lastAngleL, angleL)
            angDispL += dThetaL

            dThetaR = computeDeltaThetaDeg(lastAngleR, angleR)
            angDispR += dThetaR
            
            print(f"Displacement: {angDispL:.2f} {angDispR:.2f}")

            lastAngleL, lastAngleR = angleL, angleR

            # Ensure the delta theta is greater than the error
            # in the encoder measurements
            sleep(0.05)
    except KeyboardInterrupt:
        drive(0)
        print("Navi: Stopping")
        raise

def driveToAngularDisplacement(targetAngDispL: float, targetAngDispR: float,
                               logSession: dl.DataLogSession):
    angDispSignL, angDispSignR = np.sign(targetAngDispL), np.sign(targetAngDispR)

    dutyCycle = 0.8
    if angDispSignL != angDispSignR:
        dutyCycle = 1.0

    motorSpeedL, motorSpeedR = dutyCycle * angDispSignL, dutyCycle * angDispSignR
    
    doneL, doneR = False, False
    angDispL, angDispR = 0, 0
    
    lastAngleL, lastAngleR = readShaftPositions()
    lastTargetDeltaL, lastTargetDeltaR = np.nan, np.nan

    dataEntries = []

    try:
        #print("Entering step loop...")
        while not (doneL and doneR):
            # Compute the remaining angular displacement
            targetDeltaL, targetDeltaR = targetAngDispL - angDispL, targetAngDispR - angDispR
            #print(f"Disp remaining: {targetDeltaL:.1f} {targetDeltaR:.1f}\t\t{motorSpeedL:.1f} {motorSpeedR:.1f}")

            if isTargetReached(lastTargetDeltaL, targetDeltaL, 0.01):
                doneL = True
                motorSpeedL = 0.0
            driveRight(motorSpeedL)

            if isTargetReached(lastTargetDeltaR, targetDeltaR, 0.01):
                doneR = True
                motorSpeedR = 0.0
            driveLeft(motorSpeedR)

            if doneL and doneR:
                break

            angleL, angleR = readShaftPositions()
            
            # Handle when angle overflows (crossing 0 deg)
            dThetaL = computeDeltaThetaDeg(lastAngleL, angleL)
            angDispL += dThetaL

            dThetaR = computeDeltaThetaDeg(lastAngleR, angleR)
            angDispR += dThetaR
            #print(f"Delta Theta: {dThetaL:.1f} {dThetaR:.1f}")

            lastAngleL, lastAngleR = angleL, angleR
            lastTargetDeltaL, lastTargetDeltaR = targetDeltaL, targetDeltaR

            # Ensure the delta theta is greater than the error
            # in the encoder measurements
            sleep(0.05)

            dataEntries.append([angleL, angleR, angDispL, angDispR, dThetaL, dThetaR])
    except KeyboardInterrupt:
        drive(0)
        print("Navi: Stopping")
        raise
    if logSession is not None:
        for entry in dataEntries:
            logSession.writeEntry(entry)

def isTargetReached(previous: float, current: float, tolerance: float) -> bool:
    # If we're already within the specified tolerance, we're golden
    if np.abs(current) <= tolerance:
        return True
    
    # If the previous delta has a different sign than the current
    # delta, then by the intermediate value theorem we must have
    # passed zero delta
    if not np.isnan(previous):
        return bool(np.sign(previous) != np.sign(current))
    
    return False

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
