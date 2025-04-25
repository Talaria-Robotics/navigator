from queue import Queue
from floormap import FloorMap
from mail_route_events import *
from models import *
from svgpathtools import Path
from typing import Callable
from nav_utils import Pose, discretizePath, normalizeHeading
from odometry import computeWheelAnglesForTurn, computeWheelAnglesForForward, computeDeltaThetaDeg
from obstacle_avoidance import nearestWithinBox
import data_log as dl
from vector import cart2polar
import numpy as np
from time import sleep

MOCK = False

if not MOCK:
    from motor import drive, driveLeft, driveRight, initMotors
    from encoder import readShaftPositions
    initMotors()
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
    botState = Pose()
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
                    
                    emitEvent(arrivedAtStopEvent)
                    statusesSent += 1

                    waitForConfirmation()

            if stopQueue.empty():
                nextStopId = None
                print("Stop queue was empty, going home!")
            else:
                nextStopId = stopQueue.get()
            
        # Let the UI know we're going to a new stop
        roomName = floorplan.rooms[nextStopId]
        print(f"Next stop: {roomName} ({nextStopId})")
        room = MailRouteRoom(nextStopId, roomName)
        inTransitEvent = InTransitEvent(room)
        inTransitEvent.orderNumber = statusesSent
        
        emitEvent(inTransitEvent)
        statusesSent += 1

        pathToFollow: Path = floorplan.getShortestAdjacentPath(currentNodeId, nextNodeId)
        botState = follow_path(botState, pathToFollow, None)

def follow_path(botState: Pose, path: Path, logSession: dl.DataLogSession) -> Pose:
    # Configure data logging
    if logSession:
        logSession.writeHeaders(["angleL", "angleR", "angDispL", "angDispR", "dThetaL", "dThetaR"])

    segments = discretizePath(path)
    for targetState in segments:
        # Compute correction for position in polar coordinates
        positionCorrection = targetState.pos - botState.pos
        positionForwardCorrection, positionHeadingTarget = cart2polar(positionCorrection)
        positionHeadingCorrection = positionHeadingTarget - botState.dir
        
        # If the magnitude of the angle is greater than 180°,
        # just turn the opposite direction
        positionHeadingCorrection = normalizeHeading(positionHeadingCorrection)

        # Correct heading angle for position
        print(f"Correct forward heading: {positionHeadingCorrection:.1f}°")
        targetAngDispL, targetAngDispR = computeWheelAnglesForTurn(positionHeadingCorrection)
        actualAngDispL, actualAngDispR = driveToAngularDisplacement(targetAngDispL, targetAngDispR, logSession)
        #botState = computePoseFromWheelAngles(botState, actualAngDispL, actualAngDispR)

        # Correct forward distance
        print(f"Correct forward distance: {positionForwardCorrection:.2f}\"")
        targetAngDispL, targetAngDispR = computeWheelAnglesForForward(positionForwardCorrection)
        actualAngDispL, actualAngDispR = driveToAngularDisplacement(targetAngDispL, targetAngDispR, logSession)
        #botState = computePoseFromWheelAngles(botState, actualAngDispL, actualAngDispR)

        # Correct heading angle for final heading
        print(f"Correct final heading: {positionHeadingCorrection:.1f}°")
        targetAngDispL, targetAngDispR = computeWheelAnglesForForward(targetState.dir - positionHeadingTarget)
        actualAngDispL, actualAngDispR = driveToAngularDisplacement(targetAngDispL, targetAngDispR, logSession)
        #botState = computePoseFromWheelAngles(botState, actualAngDispL, actualAngDispR)
        
        # TODO: Update pose with real data
        botState = targetState

    print(f"Bot state: {botState}")
    return botState

def trackDisplacementWhile(action: Callable[..., bool]) -> tuple[float, float]:
    angDispL, angDispR = 0, 0
    lastAngleL, lastAngleR = readShaftPositions()

    while action():
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
    return angDispL, angDispR

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

            reachedTargetL = isTargetReached(lastTargetDeltaL, targetDeltaL, 0.01)
            if reachedTargetL:
                doneL = True
                motorSpeedL = 0.0

            reachedTargetR = isTargetReached(lastTargetDeltaR, targetDeltaR, 0.01)
            if reachedTargetR:
                doneR = True
                motorSpeedR = 0.0
            
            # This in intentionally swapped.
            driveRight(motorSpeedL)
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

            # Stop if obstacles are detected
            while len(list(nearestWithinBox())) > 3:
               drive(0)
               print("Obstacle detected")
               sleep(0.5)
               pass

    except KeyboardInterrupt:
        drive(0)
        print("Navi: Stopping")
        raise
    if logSession is not None:
        for entry in dataEntries:
            logSession.writeEntry(entry)
    
    # Return the actual angular displacement for future calculations
    return angDispL, angDispR

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
        input("Waiting for confirmation...")

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
