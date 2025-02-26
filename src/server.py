from asyncio import sleep
from models import *
from mail_route_events import *
from floormap import FloorMap
from sanic import Sanic, text, json, Request, Websocket
from orjson import dumps, loads
from queue import SimpleQueue
import os

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

@app.websocket("/transitFeed")
async def transitFeed(request: Request, ws: Websocket):
    print("Connected to Control Panel")
    statusesSent = 0
    
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
    
    while True:
        while not app.ctx.events.empty():
            event: MailRouteEvent = app.ctx.events.get()
            event.orderNumber = statusesSent
            
            eventStr = dumps(event, default=vars).decode("utf-8")
            print(f"Sending event '{eventStr}'")
            await ws.send(eventStr)
            print(f"Sent #{statusesSent}")
            statusesSent += 1
            
            if type(event) is ArrivedAtStopEvent:
                # Wait for recipient to confirm
                confirmationData = await ws.recv()
                print(f"Package received: '{confirmationData}'")
            else:
                # DEMO
                await sleep(4)
                # END DEMO
            

@app.post("/confirmDelivery")
async def confirmDelivery(request: Request):
    raise NotImplementedError()
