# Multi-Format Autonomous AI System

A FastAPI-based system that processes and analyzes various types of business documents and communications using AI agents.

## Features

- Process and analyze emails, PDFs, and JSON data
- Automatic format detection and classification
- Intelligent routing to specialized agents
- Activity logging and tracking
- Risk assessment and action triggering

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (optional):
Create a `.env` file in the root directory:
```
DATABASE_URL=memory/activity_log.db
```

4. Run the server:
```bash
python main.py
```

The server will start at `http://localhost:8000`

## API Endpoints

### 1. Process Input (POST /process)

Processes various types of inputs (email, PDF, JSON) and returns analysis.

#### Email Processing (Professional Tone)
```json
// Request
{
    "email_content": "From: hr@company.com\nSubject: Interview Invitation\n\nDear John,\n\nWe are pleased to invite you for an interview for the Software Engineer position at our New York office. Please reply with your availability by Friday.\n\nBest regards,\nHR Team."
}

// Expected Response
{
    "Sender email address": "hr@company.com",
    "Urgency level": "medium",
    "Tone": "polite",
    "Key points or requests": "Invitation for an interview for the Software Engineer position at the New York office. Request to reply with availability by Friday."
}
```
#### Email Processing (Threatening Tone)
```json
// Request
{
  "email_content": "From: furious.customer@mail.com\nSubject: You Better Fix This Now\n\nI’m tired of being ignored. If this issue isn’t fixed today, I’ll make sure your company’s reputation is ruined across every review site."
}

// Expected Response
{
    "Sender email address": "furious.customer@mail.com",
    "Urgency level": "high",
    "Tone": "threatening",
    "Key points or requests": "Issue must be fixed today or threatens to ruin company's reputation on review sites"
}
```

#### JSON Processing
```json
// Request
{
       "json_data": "{\"event_type\": \"unauthorized_access\", \"timestamp\": \"2024-03-15T10:30:00Z\", \"source\": \"security_system\", \"data\": {\"id\": \"123\", \"user_id\": \"user456\", \"ip_address\": \"192.168.1.1\", \"attempted_resource\": \"/api/admin\"}}"
}

// Expected Response
{
    "is_valid": true,
    "data": {
        "event_type": "unauthorized_access",
        "timestamp": "2024-03-15T10:30:00Z",
        "source": "security_system",
        "data": {
            "id": "123",
            "user_id": "user456",
            "ip_address": "192.168.1.1",
            "attempted_resource": "/api/admin",
            "amount": null,
            "location": null,
            "device_info": null
        }
    },
    "anomalies": [
        "suspicious_event: unauthorized_access",
        "stale_event"
    ],
    "risk_level": "medium",
    "action_triggered": "POST /risk_alert/medium",
    "action_result": {
        "status": "unknown_action",
        "action": "POST /risk_alert/medium"
    }
}
```

#### PDF Processing
```json
// Request (multipart/form-data)
// Key: file
// Value: PDF file
// Content-Type: application/pdf

// Expected Response
{
    "document_type": "invoice",
    "key_terms": ["Payment Terms", "Due Date"],
    "important_dates": ["2024-04-01"],
    "monetary_amounts": ["15000.00"],
    "regulatory_references": [],
    "action_triggered": "POST /risk_alert"
}
```

### 2. Get All Activities (GET /activity)

Retrieves all logged activities.

```json
// Request
GET /activity

// Expected Response
[
    {
        "source": "email",
        "timestamp": "2024-03-15T10:30:00Z",
        "classification": {
            "format": "email",
            "intent": "communication"
        },
        "extracted_fields": {
            "sender": "sender@example.com",
            "urgency": "low",
            "tone": "neutral",
            "key_points": ["Test email content"]
        },
        "action_triggered": null,
        "agent_trace": ["classifier_agent", "email_agent"]
    }
]
```

### 3. Get Activity by ID (GET /activity/{activity_id})

Retrieves a specific activity by ID.

```json
// Request
GET /activity/1

// Expected Response
{
    "source": "email",
    "timestamp": "2024-03-15T10:30:00Z",
    "classification": {
        "format": "email",
        "intent": "communication"
    },
    "extracted_fields": {
        "sender": "sender@example.com",
        "urgency": "low",
        "tone": "neutral",
        "key_points": ["Test email content"]
    },
    "action_triggered": null,
    "agent_trace": ["classifier_agent", "email_agent"]
}
```

## Error Responses

```json
// 400 Bad Request
{
    "detail": "Invalid email format"
}

// 404 Not Found
{
    "detail": "Activity not found"
}

// 500 Internal Server Error
{
    "detail": "Error message here"
}
```

## Testing with curl

1. Email Processing:
```bash
curl -X POST "http://localhost:8000/process" \
     -H "Content-Type: application/json" \
     -d '{"email_content": "From: sender@example.com\nSubject: Test Email\n\nThis is a test email content."}'
```

2. JSON Processing:
```bash
curl -X POST "http://localhost:8000/process" \
     -H "Content-Type: application/json" \
     -d '{"json_data": "{\"event_type\": \"unauthorized_access\", \"timestamp\": \"2024-03-15T10:30:00Z\"}"}'
```

3. PDF Processing:
```bash
curl -X POST "http://localhost:8000/process" \
     -F "file=@/path/to/your/file.pdf"
```

4. Get All Activities:
```bash
curl "http://localhost:8000/activity"
```

5. Get Specific Activity:
```bash
curl "http://localhost:8000/activity/1"
```

## System Flow

1. Input is received through the `/process` endpoint
2. The classifier agent determines the format and intent
3. The input is routed to the appropriate specialized agent:
   - Email Agent: Analyzes email content, tone, and urgency
   - PDF Agent: Extracts information from PDF documents
   - JSON Agent: Validates and analyzes JSON data
4. If needed, the action router triggers appropriate actions
5. All activities are logged in the memory store

## Project Structure

```
.
├── agents/
│   ├── base_agent.py
│   ├── classifier_agent.py
│   ├── email_agent.py
│   ├── json_agent.py
│   ├── pdf_agent.py
│   └── action_router.py
├── memory/
│   └── memory_store.py
├── tests/
├── main.py
├── requirements.txt
└── README.md
```

## Dependencies

- FastAPI
- LangChain
- OpenAI
- PyPDF2
- SQLite3
- Pydantic

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 