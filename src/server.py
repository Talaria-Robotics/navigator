from asyncio import sleep
from models import *
from floormap import FloorMap
from sanic import Sanic, text, json, Request, Websocket
from orjson import dumps, loads
from queue import SimpleQueue

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
    requestedRoute: str
    events: SimpleQueue = SimpleQueue()

ctx = NavigatorContext()
ctx.floorplan = FloorMap(r".\maps\TestA.floormap")
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
    floorplan = FloorMap(r".\maps\TestA.floormap")

    routeInfo = PossibleMailRouteInfo()
    routeInfo.id = floorplan.id
    routeInfo.name = floorplan.name

    routeInfo.rooms = [
        MailRouteRoom(id, name)
        for id, name in floorplan.rooms.items()
    ]

    routeInfo.bins = [
        MailBin(1, "Letter Slot 1"),
        MailBin(2, "Letter Slot 2"),
        MailBin(3, "Letter Slot 3"),
        MailBin(4, "Package Area"),
    ]

    return json(routeInfo)

@app.post("/route")
async def setRoute(request: Request):
    print(request.json)
    app.ctx.requestedRoute = request.json
    return json(request.json)

@app.get("/routeStatus")
async def getRouteStatus(request: Request):
    return text(str(app.ctx.events))

@app.websocket("/transitFeed")
async def transitFeed(request: Request, ws: Websocket):
    print("Connected to Control Panel")
    stausesSent = 0
    app.ctx.events.put("{ \"orderNumber\": 0, \"$type\": \"ReturnHome\" }")
    app.ctx.events.put("{\"$type\":\"InTransit\",\"orderNumber\":1,\"room\":{\"id\":\"room1\",\"name\":\"Room 1\"}}")
    app.ctx.events.put("{\"$type\":\"ArrivedAtStop\",\"orderNumber\":2,\"room\":{\"id\":\"room1\",\"name\":\"Room 1\"},\"bin\":{\"number\":2,\"name\":\"Letter Slot 1\"}}")
    app.ctx.events.put("{\"$type\":\"InTransit\",\"orderNumber\":3,\"room\":{\"id\":\"room2\",\"name\":\"Room 2\"}}")
    app.ctx.events.put("{\"$type\":\"ArrivedAtStop\",\"orderNumber\":4,\"room\":{\"id\":\"room2\",\"name\":\"Room 2\"},\"bin\":{\"number\":3,\"name\":\"Letter Slot 2\"}}")
    app.ctx.events.put("{ \"orderNumber\": 5, \"$type\": \"ReturnHome\" }")
    while True:
        while not app.ctx.events.empty():
            s = app.ctx.events.get()
            print(f"Sending event '{s}'")
            await ws.send(s)
            await sleep(4)
            stausesSent += 1

@app.post("/confirmDelivery")
async def confirmDelivery(request: Request):
    raise NotImplementedError()