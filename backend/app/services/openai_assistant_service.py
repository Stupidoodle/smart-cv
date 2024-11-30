import openai
from typing import List, Dict, Any, Optional

from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Message, Run
from pydantic import BaseModel

from app.services.ai_base import AIBase
from app.core.config import settings
import time


class OpenAIAssistantService(AIBase):
    def __init__(self):
        openai.api_key = settings.OPEN_AI_API_KEY

    def create_assistant(
        self,
        name: str,
        instructions: str,
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Assistant:
        assistant = openai.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools,
            response_format=(response_format if response_format else None),
        )
        return assistant

    @staticmethod
    def list_assistants() -> List[Assistant]:
        assistants = openai.beta.assistants.list()
        return assistants

    def create_thread(self) -> Thread:
        thread = openai.beta.threads.create()
        return thread

    def add_message_to_thread(self, thread_id: str, role: str, content: str) -> Message:
        message = openai.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content,
        )
        return message

    def run_assistant_on_thread(
        self,
        thread_id: str,
        assistant_id: Optional[str] = None,
        run_id: Optional[str] = None,
        instructions: Optional[str] = None,
        tool_outputs: Optional[List[Dict[str, Any]]] = None,
    ) -> Run:
        if tool_outputs:
            run = openai.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread_id,
                run_id=run_id,  # Ensure run_id is passed correctly
                tool_outputs=tool_outputs,
            )
        else:
            run = openai.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=assistant_id,
                instructions=instructions,
            )
        return run

    @staticmethod
    def cancel_run(run_id: str, thread_id: str):
        try:
            openai.beta.threads.runs.cancel(run_id=run_id, thread_id=thread_id)
        except Exception as e:
            print(f"Error cancelling run: {e}")

    def list_messages_in_thread(self, thread_id: str) -> List[Message]:
        messages = openai.beta.threads.messages.list(
            thread_id=thread_id
        ).data  # NOTE: This might return this weird ass SyncCursorPage so we need to
        # type
        # cast it
        return messages
