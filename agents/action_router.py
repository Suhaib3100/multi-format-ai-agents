from typing import Dict, Any, List
import requests
from .base_agent import BaseAgent

class ActionRouter(BaseAgent):
    def __init__(self):
        super().__init__("action_router")
        self.action_handlers = {
            "POST /crm/escalate": self._handle_escalation,
            "POST /risk_alert": self._handle_risk_alert,
            "POST /log_event": self._handle_log_event
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and route to appropriate actions."""
        action_triggered = input_data.get("action_triggered")
        if not action_triggered:
            return {"status": "no_action_needed"}

        # Get the handler for the action
        handler = self.action_handlers.get(action_triggered)
        if not handler:
            return {"status": "unknown_action", "action": action_triggered}

        # Execute the action
        try:
            result = handler(input_data)
            
            # Log the action execution
            self.log_activity(
                source="action_router",
                classification={"format": "action", "intent": action_triggered},
                extracted_fields={
                    "input_data": input_data,
                    "action_result": result
                },
                action_triggered=action_triggered
            )
            
            return result
        except Exception as e:
            error_result = {
                "status": "error",
                "action": action_triggered,
                "error": str(e)
            }
            
            # Log the error
            self.log_activity(
                source="action_router",
                classification={"format": "action", "intent": action_triggered},
                extracted_fields={
                    "input_data": input_data,
                    "error": str(e)
                },
                action_triggered=action_triggered
            )
            
            return error_result

    def _handle_escalation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CRM escalation requests."""
        # In a real system, this would make an actual API call
        # For now, we'll simulate the response
        return {
            "status": "success",
            "message": "Escalation request processed",
            "ticket_id": "ESC-12345"
        }

    def _handle_risk_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle risk alert requests."""
        # In a real system, this would make an actual API call
        # For now, we'll simulate the response
        return {
            "status": "success",
            "message": "Risk alert created",
            "alert_id": "RISK-67890"
        }

    def _handle_log_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle event logging requests."""
        # In a real system, this would make an actual API call
        # For now, we'll simulate the response
        return {
            "status": "success",
            "message": "Event logged successfully",
            "log_id": "LOG-54321"
        } 