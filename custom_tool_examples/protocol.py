# communication_protocol.py
import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, Callable, Coroutine
from pydantic import BaseModel, Field
from datetime import datetime

class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender: str
    receiver: str
    message_type: str
    payload: Dict[str, Any]
    in_reply_to: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class CommunicationProtocol:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CommunicationProtocol, cls).__new__(cls)
            cls._instance.message_queue = asyncio.Queue()
            cls._instance.running = False
            cls._instance._message_handlers: Dict[str, Callable[[Message], Coroutine[Any, Any, None]]] = {}
            # The old response mechanism, kept for non-streaming parts of the app if any.
            cls._instance.response_events: Dict[str, asyncio.Event] = {}
            cls._instance.responses: Dict[str, Any] = {}
            # New mechanism for streaming responses to endpoints.
            cls._instance.subscribers: Dict[str, asyncio.Queue] = {}
        logging.info("Communication Protocol Initialized.")
        return cls._instance

    def register_handler(self, receiver_id: str, handler: Callable[[Message], Coroutine[Any, Any, None]]):
        logging.info(f"Registering handler for receiver: {receiver_id}")
        self._message_handlers[receiver_id.lower()] = handler

    async def send_message(self, message: Message):
        logging.debug(f"Enqueueing message: {message.message_id} for {message.receiver}")
        await self.message_queue.put(message)

    async def _route_message(self, message: Message):
        receiver = message.receiver.lower()
        
        # If an endpoint is subscribed to this conversation, send the message to it.
        # This is the primary mechanism for streaming responses.
        if message.conversation_id in self.subscribers:
            await self.subscribers[message.conversation_id].put(message)

        # The legacy mechanism for single, final responses.
        if receiver == "frontend":
            if message.conversation_id in self.response_events:
                self.responses[message.conversation_id] = message
                self.response_events[message.conversation_id].set()
            # Stop further processing if it's a frontend message.
            return

        handler = self._message_handlers.get(receiver)
        if handler:
            logging.debug(f"Routing message {message.message_id} to handler for {receiver}")
            await handler(message)
        else:
            logging.warning(f"No handler registered for receiver: {receiver}. Message ID: {message.message_id}")

    async def run(self):
        self.running = True
        logging.info("Communication Protocol Runner starting...")
        while self.running:
            try:
                message = await self.message_queue.get()
                await self._route_message(message)
                self.message_queue.task_done()
            except asyncio.CancelledError:
                logging.info("Message processing loop cancelled.")
                self.running = False
                break
        logging.info("Communication Protocol Runner stopped.")

    def stop(self):
        self.running = False

    async def get_response(self, conversation_id: str, timeout: int = 30) -> Optional[Message]:
        """Waits for a response for a specific conversation_id."""
        self.response_events[conversation_id] = asyncio.Event()
        try:
            await asyncio.wait_for(self.response_events[conversation_id].wait(), timeout=timeout)
            return self.responses.pop(conversation_id, None)
        except asyncio.TimeoutError:
            logging.warning(f"Timeout waiting for response for conversation_id: {conversation_id}")
            return None
        finally:
            self.response_events.pop(conversation_id, None)

    # --- New Methods for Streaming ---
    def subscribe_to_conversation(self, conversation_id: str) -> asyncio.Queue:
        """
        Allows an endpoint to subscribe to all messages for a specific conversation.
        """
        logging.debug(f"Endpoint subscribing to conversation: {conversation_id}")
        queue = asyncio.Queue()
        self.subscribers[conversation_id] = queue
        return queue

    def unsubscribe_from_conversation(self, conversation_id: str):
        """
        Removes the subscription queue for a conversation.
        """
        logging.debug(f"Endpoint unsubscribing from conversation: {conversation_id}")
        self.subscribers.pop(conversation_id, None)


def get_communication_protocol():
    return CommunicationProtocol()

# Example Usage (Conceptual - would be in your main setup)
async def example_assistant_handler(message: Message):
    print(f"Assistant Agent received message: {message}")
    # Here the assistant agent would use its LLM router to decide the next step
    # and potentially send new messages via `protocol.send_message`
    pass

async def main():
    # Configure logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    protocol = get_communication_protocol()
    
    # Start the protocol runner in the background
    runner_task = asyncio.create_task(protocol.run())
    
    # Example: Simulate sending a message from a 'Frontend' component
    initial_message = Message(
        sender="Frontend",
        receiver="Assistance", # Route to the main assistant
        message_type="user_query",
        payload={"query": "Analyze my data"},
        conversation_id="conv_123"
    )
    await protocol.send_message(initial_message)
    
    # Let it run for a bit
    await asyncio.sleep(2)
    
    # Stop the protocol
    protocol.stop()
    await runner_task # Wait for the runner to finish

# if __name__ == "__main__":
#     asyncio.run(main()) # Uncomment to run example