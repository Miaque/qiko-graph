import logging
from datetime import datetime

import socketio

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode="asgi",
    transports=["websocket", "polling"],
    allow_upgrades=True,
    always_connect=True,
)

socket_app = socketio.ASGIApp(socketio_server=sio, socketio_path="/ws/socket.io")


@sio.event
async def connect(sid, environ):
    logger.info(f"客户端连接: {sid}")
    # 发送当前时间给客户端
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await sio.emit("time", {"time": current_time}, room=sid)


@sio.event
async def disconnect(sid):
    logger.info(f"客户端断开连接: {sid}")


@sio.on("query")
async def test_message(sid, message):
    print(message)
    await sio.emit("chat", {"data": message + " -Interaction Engine"}, room=sid)
