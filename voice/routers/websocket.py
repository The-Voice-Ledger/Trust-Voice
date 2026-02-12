"""
WebSocket Router for Real-Time Updates

Provides live donation feed and campaign progress updates
to the web frontend via WebSocket connections.
"""

import json
import logging
import asyncio
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages active WebSocket connections grouped by channel."""
    
    def __init__(self):
        # channel_name -> set of websocket connections
        self.channels: dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.channels:
            self.channels[channel] = set()
        self.channels[channel].add(websocket)
        logger.info(f"WebSocket connected to channel '{channel}' ({len(self.channels[channel])} clients)")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.channels:
            self.channels[channel].discard(websocket)
            if not self.channels[channel]:
                del self.channels[channel]
    
    async def broadcast(self, channel: str, data: dict):
        """Broadcast a message to all clients in a channel."""
        if channel not in self.channels:
            return
        
        message = json.dumps(data, default=str)
        dead_connections = set()
        
        for ws in self.channels[channel]:
            try:
                await ws.send_text(message)
            except Exception:
                dead_connections.add(ws)
        
        # Clean up dead connections
        for ws in dead_connections:
            self.channels[channel].discard(ws)


# Singleton manager
manager = ConnectionManager()


@router.websocket("/ws/donations")
async def donations_feed(websocket: WebSocket):
    """
    Real-time donation feed.
    
    Clients receive messages when new donations are created:
    {
        "type": "new_donation",
        "donation_id": 42,
        "campaign_id": 5,
        "campaign_title": "Clean Water",
        "amount": 25.00,
        "currency": "USD",
        "donor_name": "Anonymous",
        "timestamp": "2026-02-12T10:30:00"
    }
    """
    await manager.connect(websocket, "donations")
    try:
        while True:
            # Keep connection alive — client can send ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, "donations")


@router.websocket("/ws/campaign/{campaign_id}")
async def campaign_feed(websocket: WebSocket, campaign_id: int):
    """
    Real-time updates for a specific campaign.
    
    Clients receive:
    - New donations to this campaign
    - Progress milestones (25%, 50%, 75%, 100%)
    - Video upload notifications
    """
    channel = f"campaign_{campaign_id}"
    await manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


async def notify_new_donation(donation_data: dict):
    """
    Called from the donation creation endpoint to broadcast.
    
    Args:
        donation_data: {
            "donation_id", "campaign_id", "campaign_title",
            "amount", "currency", "donor_name", "timestamp"
        }
    """
    payload = {"type": "new_donation", **donation_data}
    
    # Broadcast to global donations feed
    await manager.broadcast("donations", payload)
    
    # Broadcast to campaign-specific channel
    campaign_id = donation_data.get("campaign_id")
    if campaign_id:
        await manager.broadcast(f"campaign_{campaign_id}", payload)
