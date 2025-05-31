from typing import Dict, Any, List
import requests
from .base_agent import BaseAgent
import logging
import json

logger = logging.getLogger(__name__)

class ActionRouter(BaseAgent):
    def __init__(self):
        super().__init__("action_router")
        # Map triggered actions to internal handler methods
        self.action_handlers = {
            # Example CRM escalation (if an agent triggers this specifically)
            "POST /crm/escalate": self._handle_crm_escalation,
            
            # Risk Alerts based on severity
            "POST /risk_alert": self._handle_general_risk_alert,       # General risk alert
            "POST /risk_alert/high": self._handle_high_risk_alert,     # High risk, e.g., Escalate issue
            "POST /risk_alert/critical": self._handle_critical_risk_alert # Critical risk, e.g., Create ticket/Flag compliance risk
            
            # Example event logging (if an agent triggers this specifically)
            # "POST /log_event": self._handle_log_event # Keeping for reference, agents don't currently trigger this
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and route to appropriate actions."""
        action_triggered = input_data.get("action_triggered")
        
        if not action_triggered:
            logger.info("ActionRouter: No action triggered.")
            return {"status": "no_action_needed"}

        logger.info(f"ActionRouter: Attempting to handle action: {action_triggered}")

        # Get the handler for the action
        handler = self.action_handlers.get(action_triggered)
        
        if not handler:
            logger.warning(f"ActionRouter: No handler found for action: {action_triggered}")
            return {"status": "unknown_action", "action": action_triggered}

        # Execute the action
        try:
            logger.info(f"ActionRouter: Executing handler for {action_triggered}")
            result = handler(input_data)
            
            # Log the action execution
            self.log_activity(
                source="action_router",
                classification={"format": "action", "intent": action_triggered, "status": result.get("status", "completed")},
                extracted_fields={
                    "input_data_summary": {k: v for k, v in input_data.items() if k != 'agent_trace'}, # Log summary of input data
                    "action_result": result
                },
                action_triggered=action_triggered,
                agent_trace=[f"Action Handled: {action_triggered}"] # Log trace within action router
            )
            
            logger.info(f"ActionRouter: Action {action_triggered} completed with status {result.get('status')}")
            return result
            
        except Exception as e:
            logger.error(f"ActionRouter: Error executing handler for {action_triggered}: {str(e)}")
            error_result = {
                "status": "error",
                "action": action_triggered,
                "error": str(e)
            }
            
            # Log the error
            self.log_activity(
                source="action_router",
                classification={"format": "action", "intent": action_triggered, "status": "error"},
                extracted_fields={
                    "input_data_summary": {k: v for k, v in input_data.items() if k != 'agent_trace'}, # Log summary of input data
                    "error": str(e)
                },
                action_triggered=action_triggered # Log the attempted action even on error
            )
            
            return error_result

    def _handle_crm_escalation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate handling a CRM escalation request."""
        logger.info("ActionRouter: Simulating CRM escalation...")
        # In a real system, this would make an actual API call to a CRM system
        # For now, we'll simulate the response
        return {
            "status": "success",
            "action_simulated": "POST to CRM API",
            "message": "Simulated: Escalation ticket created in CRM",
            "ticket_id": f"CRM-TICKET-{hash(json.dumps(data)) % 100000}" # Generate a simple fake ticket ID
        }

    def _handle_general_risk_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate handling a general risk alert."""
        logger.info("ActionRouter: Simulating General Risk Alert...")
        # Simulate logging a general alert or notification
        return {
            "status": "success",
            "action_simulated": "POST to Risk Alert System (General)",
            "message": "Simulated: General risk alert logged or notification sent."
        }

    def _handle_high_risk_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate handling a high risk alert (e.g., escalate issue)."""
        logger.info("ActionRouter: Simulating High Risk Alert - Escalating Issue...")
        # Simulate escalating the issue within a system
        return {
            "status": "success",
            "action_simulated": "POST to Risk Alert System (High) / Escalation System",
            "message": "Simulated: High risk issue escalated.",
             "escalation_ref": f"ESCALATION-{hash(json.dumps(data)) % 100000}" # Simulate an escalation reference
        }

    def _handle_critical_risk_alert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate handling a critical risk alert (e.g., create ticket, flag compliance)."""
        logger.info("ActionRouter: Simulating Critical Risk Alert - Creating Ticket / Flagging Compliance...")
        # Simulate creating a high-priority ticket and flagging for compliance review
        return {
            "status": "success",
            "action_simulated": "POST to Risk Alert System (Critical) / Ticketing / Compliance System",
            "message": "Simulated: Critical risk ticket created and compliance flagged.",
            "ticket_id": f"CRITICAL-TICKET-{hash(json.dumps(data)) % 100000}", # Simulate a critical ticket ID
            "compliance_flagged": True
        }

    # Keeping for reference, agents don't currently trigger this
    # def _handle_log_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
    #     """Handle event logging requests."""
    #     logger.info("ActionRouter: Simulating Log Event...")
    #     # Simulate logging an event to a separate logging service
    #     return {
    #         "status": "success",
    #         "action_simulated": "POST to Logging Service",
    #         "message": "Simulated: Event logged successfully."
    #     } 