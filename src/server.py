from models import *
from mail_route_events import *
from floormap import FloorMap
from sanic import Config, Sanic, text, json, Request
from orjson import dumps, loads
from queue import SimpleQueue
from path_following import transitFeed
import threading
import socket
import os

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
    abortTransitFeed: bool

ctx = NavigatorContext()
ctx.abortTransitFeed = False
ctx.floorplan = FloorMap(os.path.join("maps", "PIC_Sample_Map.floormap"))
ctx.bins = {
    1: "Letter Slot 1",
    2: "Letter Slot 2",
    3: "Letter Slot 3",
    14: "Package Area",
}

NavigatorApp = Sanic[Config, NavigatorContext]

app: NavigatorApp = Sanic("talaria_navigator",
    dumps=custom_dumps, loads=loads,
    ctx=ctx)    

@app.get("/health")
async def health(request: Request):
    return text("OK")

@app.get("/possibleRoute")
async def getPossibleRouteInfo(request: Request):
    ctx: NavigatorContext = request.app.ctx
    floorplan = ctx.floorplan
    routeInfo = PossibleMailRouteInfo()
    routeInfo.id = floorplan.id
    routeInfo.name = floorplan.name

    routeInfo.rooms = [
        MailRouteRoom(id, name)
        for id, name in list(floorplan.rooms.items())[1:]
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
    
    ctx.requestedRoute = requestedRoute
    return json(request.json)

def transitFeedEntry(app: NavigatorApp):
    print("Binding to UDP socket...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Disable the timeout so we wait indefinitely for a connection
    sock.settimeout(None)
    sock.bind(("", TRANSITFEED_UDP_PORT))
    print(f"Bound to port {TRANSITFEED_UDP_PORT}")

    while not ctx.abortTransitFeed:
        msg, addr = sock.recvfrom(512)
        if not msg.startswith(b'%ready'):
            continue

        print(f"Connected to Control Panel at {addr}")

        transitFeed(ctx.requestedRoute, ctx.floorplan, ctx.bins,
                    lambda e: sendEventToSocket(e, sock, addr),
                    lambda: waitForConfirmationFromSocket(sock))

def sendEventToSocket(event: MailRouteEvent, sock: socket.socket, addr: str):
    eventStr = dumps(event, default=vars)
    print(f"Sending event '{eventStr}'")
    sock.sendto(eventStr, addr)

def waitForConfirmationFromSocket(sock: socket.socket):
    while True:
        confirmationData = sock.recv(512)
        if confirmationData.startswith(b'%acceptDelivery'):
            break

@app.main_process_stop
def shutdown_handler(app: NavigatorApp, loop):
    ctx.abortTransitFeed = True

    import motor
    motor.drive(0)

    import lidar
    lidar.disconnect()

@app.after_server_start
def init(app, loop):
    import lidar
    lidar.init()

    thread = threading.Thread(target=transitFeedEntry, args=(app,))
    thread.start()
    print("Initialization complete")

