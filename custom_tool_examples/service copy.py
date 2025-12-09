from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
from .protocol import CommunicationProtocol, Message
import logging

if TYPE_CHECKING:
    from app.services.agent_service import AgentService
    # from app.services.visualization_service import VisualizationTool

log = logging.getLogger(__name__)

class ChatProtocolService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatProtocolService, cls).__new__(cls)
            cls._instance.protocol = CommunicationProtocol()
            cls._instance.running = False
            cls._instance._protocol_task: asyncio.Task | None = None
            cls._instance.agent_service = None
            cls._instance.visualization_tool = None
        return cls._instance

    async def start(self):
        if self.running:
            return

        log.info("Starting ChatProtocolService...")
        self.running = True

        # Start the protocol message router loop
        if not self._protocol_task or self._protocol_task.done():
            self._protocol_task = asyncio.create_task(self.protocol.run())

        # Lazily import to avoid circular imports during module loading
        from app.services.agent_service import AgentService
        # from app.services.visualization_service import VisualizationTool

        if not self.agent_service:
            self.agent_service = AgentService(protocol=self.protocol)

        # VisualizationTool has been integrated directly into AgentService via VisualizationService
        # and no longer needs to be instantiated here as a standalone protocol listener.
        
        log.info("ChatProtocolService started.")

    async def stop(self):
        if not self.running:
            return

        log.info("Stopping ChatProtocolService...")
        self.running = False

        if self._protocol_task:
            self.protocol.stop()
            try:
                await self._protocol_task
            except asyncio.CancelledError:
                log.info("Protocol runner task cancelled during shutdown.")
            self._protocol_task = None

        log.info("ChatProtocolService stopped.")

    def get_protocol(self) -> CommunicationProtocol:
        return self.protocol
