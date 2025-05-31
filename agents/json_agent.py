from typing import Dict, Any, List, Optional
import json
from pydantic import BaseModel, ValidationError, Field
from datetime import datetime, timezone
from .base_agent import BaseAgent

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
        self.suspicious_events = {
            "unauthorized_access": "high",
            "data_breach": "critical",
            "system_compromise": "critical",
            "failed_login": "medium",
            "suspicious_activity": "high"
        }
        self.risk_thresholds = {
            "amount": 10000.00,
            "failed_attempts": 3,
            "suspicious_locations": ["Unknown", "High Risk Country"]
        }

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process JSON webhook data and validate its structure."""
        try:
            # Validate against schema
            validated_data = WebhookSchema(**input_data)
            
            # Check for anomalies
            anomalies = self._check_for_anomalies(validated_data)
            
            # Determine risk level and action
            risk_level = self._determine_risk_level(anomalies, validated_data)
            action_triggered = self._determine_action(risk_level, validated_data)

            # Log the analysis
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
            # Log validation errors
            self.log_activity(
                source="json",
                classification={"format": "json", "intent": "unknown", "risk_level": "high"},
                extracted_fields={"validation_errors": str(e)},
                action_triggered="POST /risk_alert",
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
        """Check for anomalies in the webhook data."""
        anomalies = []
        
        # Check event type
        if data.event_type in self.suspicious_events:
            anomalies.append(f"suspicious_event: {data.event_type}")
        
        # Check timestamp
        try:
            # Parse the timestamp and make it timezone-aware
            event_time = datetime.fromisoformat(data.timestamp.replace('Z', '+00:00'))
            # Get current time in UTC
            current_time = datetime.now(timezone.utc)
            # Compare timezone-aware datetimes
            if (current_time - event_time).total_seconds() > 3600:  # More than 1 hour old
                anomalies.append("stale_event")
        except ValueError:
            anomalies.append("invalid_timestamp")
        
        # Check data fields
        if data.data.amount and float(data.data.amount) > self.risk_thresholds["amount"]:
            anomalies.append(f"high_value: {data.data.amount}")
        
        if data.data.location in self.risk_thresholds["suspicious_locations"]:
            anomalies.append(f"suspicious_location: {data.data.location}")
        
        # Check device info
        if data.data.device_info:
            if data.data.device_info.ip_address == data.data.ip_address:
                anomalies.append("ip_mismatch")
        
        return anomalies

    def _determine_risk_level(self, anomalies: List[str], data: WebhookSchema) -> str:
        """Determine the risk level based on anomalies and event type."""
        if not anomalies:
            return "low"
        
        # Check for critical events
        if data.event_type in self.suspicious_events:
            if self.suspicious_events[data.event_type] == "critical":
                return "critical"
        
        # Count high-risk anomalies
        high_risk_count = sum(1 for a in anomalies if any(term in a for term in 
            ["suspicious_event", "high_value", "suspicious_location"]))
        
        if high_risk_count >= 2:
            return "high"
        elif high_risk_count == 1:
            return "medium"
        
        return "low"

    def _determine_action(self, risk_level: str, data: WebhookSchema) -> Optional[str]:
        """Determine the action to take based on risk level and event type."""
        if risk_level == "critical":
            return "POST /risk_alert/critical"
        elif risk_level == "high":
            return "POST /risk_alert/high"
        elif risk_level == "medium" and data.event_type in self.suspicious_events:
            return "POST /risk_alert/medium"
        return None 