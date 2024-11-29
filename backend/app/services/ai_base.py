from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from pydantic import BaseModel


class AIBase(ABC):
    @abstractmethod
    def create_assistant(
        self,
        name: str,
        instructions: str,
        model: str,
        tools: List[Dict[str, Any]],
        response_format: Optional[BaseModel],
    ) -> Dict:
        """Create a new assistant."""
        pass

    @abstractmethod
    def create_thread(self) -> Dict:
        """Create a new conversation thread."""
        pass

    @abstractmethod
    def add_message_to_thread(self, thread_id: str, role: str, content: str) -> Dict:
        """Add a message to a conversation thread."""
        pass

    @abstractmethod
    def run_assistant_on_thread(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        instructions: Optional[str] = None,
        tool_outputs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict:
        """Initiate a run of the assistant on the thread."""
        pass

    @abstractmethod
    def list_messages_in_thread(self, thread_id: str) -> List[Dict]:
        """List all messages in a conversation thread."""
        pass
