from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from typing import Dict, Any, Optional
import json
from agents.classifier_agent import ClassifierAgent
from agents.email_agent import EmailAgent
from agents.pdf_agent import PDFAgent
from agents.json_agent import JSONAgent
from agents.action_router import ActionRouter
from memory.memory_store import memory_store
from pydantic import BaseModel
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Format Autonomous AI System")

# Initialize agents
classifier = ClassifierAgent()
email_agent = EmailAgent()
pdf_agent = PDFAgent()
json_agent = JSONAgent()
action_router = ActionRouter()

class ProcessInput(BaseModel):
    email_content: Optional[str] = None
    json_data: Optional[str] = None

@app.post("/process")
async def process_input(request: Request, file: UploadFile = File(None)):
    """Process input in various formats and route to appropriate agents."""
    try:
        # Log the incoming request
        body = await request.json()
        logger.info(f"Received request body: {body}")
        
        input_data = ProcessInput(**body)
        logger.info(f"Parsed input data: {input_data}")

        # Determine input type and get content
        if file:
            content = await file.read()
            if file.content_type == "application/pdf":
                # Process PDF
                classification = classifier.process(content)
                if classification["format"] == "pdf":
                    result = pdf_agent.process(content)
                else:
                    raise HTTPException(status_code=400, detail="Invalid PDF format")
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")
        
        elif input_data.json_data:
            # Process JSON
            try:
                data = json.loads(input_data.json_data)
                classification = classifier.process(data)
                if classification["format"] == "json":
                    result = json_agent.process(data)
                else:
                    raise HTTPException(status_code=400, detail="Invalid JSON format")
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON data")
        
        elif input_data.email_content:
            # Process email
            logger.info(f"Processing email content: {input_data.email_content}")
            classification = classifier.process(input_data.email_content)
            if classification["format"] == "email":
                result = email_agent.process(input_data.email_content)
            else:
                raise HTTPException(status_code=400, detail="Invalid email format")
        
        else:
            raise HTTPException(status_code=400, detail="No input provided")

        # Route to action router if needed
        if result.get("action_triggered"):
            action_result = action_router.process(result)
            result["action_result"] = action_result

        return result

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/activity")
async def get_activity():
    """Retrieve all logged activities."""
    return memory_store.get_all_activities()

@app.get("/activity/{activity_id}")
async def get_activity_by_id(activity_id: int):
    """Retrieve a specific activity by ID."""
    activity = memory_store.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 