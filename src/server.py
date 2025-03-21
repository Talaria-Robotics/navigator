from asyncio import sleep
from models import *
from mail_route_events import *
from floormap import FloorMap
from sanic import Sanic, text, json, Request
from orjson import dumps, loads
from queue import SimpleQueue
import threading
import socket
import os
import time

TRANSITFEED_UDP_PORT = 8076

def default_serializer(obj):
    match obj:
        case Serializable():
            return obj.toJSON()
    raise TypeError

def custom_dumps(obj):
    return dumps(obj, default=default_serializer)

class NavigatorContext:
    floorplan: FloorMap
    bins: dict[int, str]
    requestedRoute: RequestedMailRoute
    events: SimpleQueue = SimpleQueue()
    transitFeedSock: socket.socket

ctx = NavigatorContext()
ctx.floorplan = FloorMap(os.path.join("maps", "TestA.floormap"))
ctx.bins = {
    1: "Letter Slot 1",
    2: "Letter Slot 2",
    3: "Letter Slot 3",
    14: "Package Area",
}

app = Sanic("talaria_navigator",
    dumps=custom_dumps, loads=loads,
    ctx=ctx)

@app.listener("before_server_start")
async def setup_udp(app):
    thread = threading.Thread(target=transitFeed)
    thread.start()

@app.get("/health")
async def health(request: Request):
    return text("OK")

@app.get("/possibleRoute")
async def getPossibleRouteInfo(request: Request):
    floorplan = app.ctx.floorplan
    routeInfo = PossibleMailRouteInfo()
    routeInfo.id = floorplan.id
    routeInfo.name = floorplan.name

    routeInfo.rooms = [
        MailRouteRoom(id, name)
        for id, name in floorplan.rooms.items()
    ]

    routeInfo.bins = [
        MailBin(number, name)
        for number, name in app.ctx.bins.items()
    ]

    return json(routeInfo)

@app.post("/route")
async def setRoute(request: Request):
    requestedRoute = RequestedMailRoute(request.json)
    print(f"Received route: {requestedRoute.stops}")
    
    app.ctx.requestedRoute = requestedRoute
    return json(request.json)

@app.get("/routeStatus")
async def getRouteStatus(request: Request):
    return text(str(app.ctx.events))

def transitFeed():
    print("Binding to UDP socket...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Disable the timeout so we wait indefinitely for a connection
    sock.settimeout(None)
    sock.bind(("", TRANSITFEED_UDP_PORT))
    print(f"Bound to port {TRANSITFEED_UDP_PORT}")

    start, addr = sock.recvfrom(512)
    print(f"Connected to Control Panel at {addr}, got {start}")

    print("Preparing route...")
    floorplan = app.ctx.floorplan
    stopIds = [*app.ctx.requestedRoute.stops.values()]
    tripStops = floorplan.planTrip(stopIds)
    print(f"Planned route: {tripStops}")

    # DEMO
    for binNumber, roomId in app.ctx.requestedRoute.stops.items():
        roomName = app.ctx.floorplan.rooms[roomId]
        room = MailRouteRoom(roomId, roomName)
        
        binName = app.ctx.bins[binNumber]
        bin = MailBin(binNumber, binName)

        app.ctx.events.put(InTransitEvent(room))
        app.ctx.events.put(ArrivedAtStopEvent(room, bin))
    
    app.ctx.events.put(ReturnHomeEvent())
    # END DEMO
    
    statusesSent = 0
    nextStopIndex = 0

    while not app.ctx.events.empty():
        event: MailRouteEvent = app.ctx.events.get()
        event.orderNumber = statusesSent
        
        eventStr = dumps(event, default=vars)
        print(f"Sending event '{eventStr}'")
        sock.sendto(eventStr, addr)
        print(f"Sent #{statusesSent}")
        statusesSent += 1
        
        if type(event) is ArrivedAtStopEvent:
            # Wait for recipient to confirm
            while True:
                confirmationData = sock.recv(512)
                if confirmationData.startswith('%'):
                    break
            print(f"Package received: '{confirmationData}'")
            nextStopIndex += 1
        else:
            # DEMO
            time.sleep(4)
            # END DEMO
