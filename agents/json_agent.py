from typing import Dict, Any, List, Optional
import json
from pydantic import BaseModel, ValidationError, Field
from datetime import datetime, timezone
from .base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

# Define Pydantic models for validating incoming JSON structure
class DeviceInfo(BaseModel):
    browser: str
    os: str
    ip_address: Optional[str] = None

class WebhookData(BaseModel):
    id: str
    user_id: str
    ip_address: str
    attempted_resource: str
    amount: Optional[float] = None
    location: Optional[str] = None
    device_info: Optional[DeviceInfo] = None

class WebhookSchema(BaseModel):
    event_type: str
    timestamp: str
    source: str
    data: WebhookData

class JSONAgent(BaseAgent):
    def __init__(self):
        super().__init__("json_agent")
        # Define events considered suspicious and their base risk level
        self.suspicious_events = {
            "unauthorized_access": "high",
            "data_breach": "critical",
            "system_compromise": "critical",
            "failed_login": "medium",
            "suspicious_activity": "high"
        }
        # Define thresholds for triggering anomalies
        self.risk_thresholds = {
            "amount": 10000.00,
            "failed_attempts": 3,
            "suspicious_locations": ["Unknown", "High Risk Country"]
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process JSON webhook data and validate its structure and assess risk."""
        try:
            # Validate the raw input dictionary against the defined schema
            validated_data = WebhookSchema(**input_data)
            
            # Check for predefined anomalies based on data content
            anomalies = self._check_for_anomalies(validated_data)
            
            # Determine the overall risk level and potential action based on anomalies and event type
            risk_level = self._determine_risk_level(anomalies, validated_data)
            action_triggered = self._determine_action(risk_level, validated_data)

            # Log the analysis result before returning
            self.log_activity(
                source="json",
                classification={
                    "format": "json",
                    "intent": validated_data.event_type,
                    "risk_level": risk_level
                },
                extracted_fields={
                    "validated_data": validated_data.dict(),
                    "anomalies": anomalies,
                    "risk_assessment": {
                        "level": risk_level,
                        "factors": [a.split(":")[0] for a in anomalies]
                    }
                },
                action_triggered=action_triggered,
                agent_trace=[
                    "Schema validation",
                    "Anomaly detection",
                    f"Risk assessment: {risk_level}",
                    f"Action triggered: {action_triggered}" if action_triggered else "No action required"
                ]
            )

            return {
                "is_valid": True,
                "data": validated_data.dict(),
                "anomalies": anomalies,
                "risk_level": risk_level,
                "action_triggered": action_triggered
            }

        except ValidationError as e:
            # Handle and log schema validation errors
            logger.error(f"JSON schema validation failed: {e}")
            self.log_activity(
                source="json",
                classification={"format": "json", "intent": "validation_error", "risk_level": "high"},
                extracted_fields={"validation_errors": str(e)},
                action_triggered="POST /risk_alert", # Trigger a risk alert for invalid data
                agent_trace=["Schema validation failed", "High risk due to invalid data"]
            )

            return {
                "is_valid": False,
                "errors": str(e),
                "anomalies": ["schema_validation_failed"],
                "risk_level": "high",
                "action_triggered": "POST /risk_alert"
            }

    def _check_for_anomalies(self, data: WebhookSchema) -> List[str]:
        """Check for specific anomaly patterns in the validated JSON data."""
        anomalies = []
        
        # Check if the event type is in the list of suspicious events
        if data.event_type in self.suspicious_events:
            anomalies.append(f"suspicious_event: {data.event_type}")
        
        # Check timestamp for staleness (more than 1 hour old) and validity
        try:
            # Parse and make event time timezone-aware (UTC)
            event_time = datetime.fromisoformat(data.timestamp.replace('Z', '+00:00'))
            # Get current UTC time
            current_time = datetime.now(timezone.utc)
            # Compare timezone-aware datetimes
            if (current_time - event_time).total_seconds() > 3600: 
                anomalies.append("stale_event")
        except ValueError:
            anomalies.append("invalid_timestamp") # Flag if timestamp format is invalid
        
        # Check data fields against risk thresholds
        if data.data.amount is not None and float(data.data.amount) > self.risk_thresholds["amount"]:
            anomalies.append(f"high_value: {data.data.amount}")
        
        if data.data.location in self.risk_thresholds["suspicious_locations"]:
            anomalies.append(f"suspicious_location: {data.data.location}")
        
        # Check if device IP matches source IP (a simple inconsistency check)
        if data.data.device_info and data.data.device_info.ip_address == data.data.ip_address:
             anomalies.append("ip_mismatch")
        
        return anomalies

    def _determine_risk_level(self, anomalies: List[str], data: WebhookSchema) -> str:
        """Determine the overall risk level based on detected anomalies and event type."""
        if not anomalies:
            return "low"
        
        # Critical if event type is critically suspicious
        if data.event_type in self.suspicious_events and self.suspicious_events[data.event_type] == "critical":
            return "critical"
        
        # Count high-impact anomalies
        high_risk_count = sum(1 for a in anomalies if any(term in a for term in 
            ["suspicious_event", "high_value", "suspicious_location"]))
        
        # Assign high or medium based on the count of high-impact anomalies
        if high_risk_count >= 2:
            return "high"
        elif high_risk_count == 1:
            return "medium"
        
        return "low" # Default to low if other conditions not met

    def _determine_action(self, risk_level: str, data: WebhookSchema) -> Optional[str]:
        """Determine which action to trigger based on the final risk level."""
        if risk_level == "critical":
            return "POST /risk_alert/critical" # Trigger critical action
        elif risk_level == "high":
            return "POST /risk_alert/high"     # Trigger high action
        elif risk_level == "medium" and data.event_type in self.suspicious_events: # Medium risk + suspicious event
            return "POST /risk_alert/medium" # Trigger medium action
        return None # No action triggered for low risk or other cases 