from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
from memory.memory_store import memory_store, ActivityLog

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.memory_store = memory_store

    def log_activity(self, source: str, classification: Dict, 
                    extracted_fields: Dict, action_triggered: str = None,
                    agent_trace: List[str] = None) -> int:
        """Log activity to the memory store."""
        if agent_trace is None:
            agent_trace = [self.name]
        else:
            agent_trace = [self.name] + agent_trace

        activity = ActivityLog(
            source=source,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            classification=classification,
            extracted_fields=extracted_fields,
            action_triggered=action_triggered,
            agent_trace=agent_trace
        )
        return self.memory_store.log_activity(activity)

    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """Process the input data and return extracted information."""
        pass

    def _add_to_trace(self, activity_id: int, agent_name: str):
        """Add an agent to the trace of an existing activity."""
        activity = self.memory_store.get_activity(activity_id)
        if activity:
            activity.agent_trace.append(agent_name)
            self.memory_store.log_activity(activity) 