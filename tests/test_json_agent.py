import pytest
from datetime import datetime, timedelta
from agents.json_agent import JSONAgent, WebhookSchema, WebhookData, DeviceInfo

@pytest.fixture
def json_agent():
    return JSONAgent()

@pytest.fixture
def valid_webhook_data():
    return {
        "event_type": "login_attempt",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "web",
        "data": {
            "id": "123",
            "user_id": "user_456",
            "ip_address": "192.168.1.1",
            "attempted_resource": "/api/v1/sensitive",
            "amount": 5000.00,
            "location": "US",
            "device_info": {
                "browser": "Chrome",
                "os": "Windows",
                "ip_address": "192.168.1.1"
            }
        }
    }

@pytest.fixture
def suspicious_webhook_data():
    return {
        "event_type": "unauthorized_access",
        "timestamp": datetime.utcnow().isoformat(),
        "source": "api",
        "data": {
            "id": "124",
            "user_id": "user_789",
            "ip_address": "10.0.0.1",
            "attempted_resource": "/api/v1/admin",
            "amount": 15000.00,
            "location": "High Risk Country",
            "device_info": {
                "browser": "Firefox",
                "os": "Linux",
                "ip_address": "10.0.0.2"  # Different from main IP
            }
        }
    }

def test_valid_webhook(json_agent, valid_webhook_data):
    result = json_agent.process(valid_webhook_data)
    
    assert result["is_valid"] is True
    assert result["risk_level"] == "low"
    assert len(result["anomalies"]) == 0
    assert result["action_triggered"] is None

def test_suspicious_webhook(json_agent, suspicious_webhook_data):
    result = json_agent.process(suspicious_webhook_data)
    
    assert result["is_valid"] is True
    assert result["risk_level"] == "high"
    assert len(result["anomalies"]) > 0
    assert "suspicious_event" in result["anomalies"][0]
    assert "high_value" in result["anomalies"][1]
    assert "suspicious_location" in result["anomalies"][2]
    assert "ip_mismatch" in result["anomalies"][3]
    assert result["action_triggered"] == "POST /risk_alert/high"

def test_stale_event(json_agent, valid_webhook_data):
    # Make the timestamp 2 hours old
    old_time = datetime.utcnow() - timedelta(hours=2)
    valid_webhook_data["timestamp"] = old_time.isoformat()
    
    result = json_agent.process(valid_webhook_data)
    
    assert result["is_valid"] is True
    assert "stale_event" in result["anomalies"]
    assert result["risk_level"] == "low"

def test_invalid_schema(json_agent):
    invalid_data = {
        "event_type": "login_attempt",
        "timestamp": "invalid_timestamp",
        "source": "web",
        "data": {
            "id": "123"
            # Missing required fields
        }
    }
    
    result = json_agent.process(invalid_data)
    
    assert result["is_valid"] is False
    assert "validation_errors" in result["errors"]
    assert result["risk_level"] == "high"
    assert result["action_triggered"] == "POST /risk_alert"

def test_critical_event(json_agent, valid_webhook_data):
    valid_webhook_data["event_type"] = "data_breach"
    
    result = json_agent.process(valid_webhook_data)
    
    assert result["is_valid"] is True
    assert result["risk_level"] == "critical"
    assert result["action_triggered"] == "POST /risk_alert/critical"

def test_medium_risk_event(json_agent, valid_webhook_data):
    valid_webhook_data["event_type"] = "failed_login"
    valid_webhook_data["data"]["amount"] = 12000.00
    
    result = json_agent.process(valid_webhook_data)
    
    assert result["is_valid"] is True
    assert result["risk_level"] == "medium"
    assert result["action_triggered"] == "POST /risk_alert/medium" 