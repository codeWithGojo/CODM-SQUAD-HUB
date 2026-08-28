from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    """Process-local WebSocket fan-out with authenticated users and explicit channels."""

    def __init__(self) -> None:
        self._user_connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self._channel_connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._socket_user: dict[WebSocket, uuid.UUID] = {}
        self._socket_channels: dict[WebSocket, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID, *, accept: bool = True) -> None:
        if accept:
            await websocket.accept()
        async with self._lock:
            self._user_connections[user_id].add(websocket)
            self._socket_user[websocket] = user_id

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            user_id = self._socket_user.pop(websocket, None)
            if user_id is not None:
                self._user_connections[user_id].discard(websocket)
                if not self._user_connections[user_id]:
                    self._user_connections.pop(user_id, None)
            for channel in self._socket_channels.pop(websocket, set()):
                self._channel_connections[channel].discard(websocket)
                if not self._channel_connections[channel]:
                    self._channel_connections.pop(channel, None)

    async def subscribe(self, websocket: WebSocket, channel: str) -> None:
        async with self._lock:
            self._channel_connections[channel].add(websocket)
            self._socket_channels[websocket].add(channel)

    async def unsubscribe(self, websocket: WebSocket, channel: str) -> None:
        async with self._lock:
            self._channel_connections[channel].discard(websocket)
            self._socket_channels[websocket].discard(channel)

    async def send_user(self, user_id: uuid.UUID, event: dict) -> None:
        await self._send_many(list(self._user_connections.get(user_id, set())), event)

    async def publish_channel(self, channel: str, event: dict) -> None:
        await self._send_many(list(self._channel_connections.get(channel, set())), event)

    async def _send_many(self, sockets: list[WebSocket], event: dict) -> None:
        stale: list[WebSocket] = []
        for socket in sockets:
            try:
                await socket.send_json(event)
            except Exception:
                stale.append(socket)
        for socket in stale:
            await self.disconnect(socket)

    @property
    def connection_count(self) -> int:
        return len(self._socket_user)


realtime = ConnectionManager()
