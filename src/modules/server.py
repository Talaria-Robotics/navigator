from modules.models import *
from sanic import Sanic, text, json
from sanic.request import Request
from sanic.response import HTTPResponse
from orjson import dumps, loads

def default_serializer(obj):
    match obj:
        case Serializable():
            return obj.toJSON()
    raise TypeError

def custom_dumps(obj):
    return dumps(obj, default=default_serializer)

app = Sanic("talaria_navigator", dumps=custom_dumps, loads=loads)

@app.get("/health")
async def health(request: Request):
    return text("OK")

@app.get("/possibleRoute")
async def getPossibleRouteInfo(request: Request):
    routeInfo = PossibleMailRouteInfo()
    routeInfo.id = "00000000-0000-0000-0000-000000000000"
    routeInfo.name = "Test Route (HTTP)"

    routeInfo.bins = [
        MailBin(1, "Letter Slot 1"),
        MailBin(2, "Letter Slot 2"),
        MailBin(3, "Letter Slot 3"),
        MailBin(4, "Package Area"),
    ]

    routeInfo.rooms = [
        MailRouteRoom("MR", "Mail Room"),
        MailRouteRoom("A", "Room A"),
        MailRouteRoom("B", "Room B"),
    ]

    return json(routeInfo)

@app.post("/route")
async def setRoute(request: Request):
    app.ctx.requestedRoute = request.json
    return json(request.json)

@app.get("/routeStatus")
async def getRouteStatus(request: Request):
    return text(app.ctx.status)

@app.post("/confirmDelivery")
async def confirmDelivery(request: Request):
    raise NotImplementedError()