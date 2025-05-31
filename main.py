from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from typing import Dict, Any, Optional
import json
from agents.classifier_agent import ClassifierAgent
from agents.email_agent import EmailAgent
from agents.pdf_agent import PDFAgent
from agents.json_agent import JSONAgent
from agents.action_router import ActionRouter
from memory.memory_store import memory_store
#from pydantic import BaseModel # No longer needed
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

# No longer needed
#class ProcessInput(BaseModel):
#    email_content: Optional[str] = None
#    json_data: Optional[str] = None

@app.post("/process")
async def process_input(request: Request):
    """Process JSON or email inputs and route to appropriate agents."""
    content_type = request.headers.get('Content-Type', '').lower()
    logger.info(f"Received request with Content-Type: {content_type}")
    
    try:
        if 'application/json' in content_type:
            logger.info("Processing as JSON...")
            # Process JSON or email input
            body = await request.json()
            logger.info(f"Received JSON body: {body}")
            
            input_data = body # Assuming the JSON structure directly matches the needed data

            if 'json_data' in input_data:
                # Process JSON
                logger.info(f"Processing json_data: {input_data['json_data']}")
                try:
                    data = json.loads(input_data['json_data'])
                    classification = classifier.process(data)
                    if classification["format"] == "json":
                        result = json_agent.process(data)
                        if not result['is_valid']:
                            raise HTTPException(status_code=400, detail=result['errors'])
                    else:
                        raise HTTPException(status_code=400, detail="Invalid JSON format")
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid JSON data")
            
            elif 'email_content' in input_data:
                # Process email
                email_content = input_data['email_content']
                logger.info(f"Processing email content: {email_content}")
                classification = classifier.process(email_content)
                if classification["format"] == "email":
                    result = email_agent.process(email_content)
                else:
                    raise HTTPException(status_code=400, detail="Invalid email format")
            
            else:
                 raise HTTPException(status_code=400, detail="No input provided in JSON body")

        else:
            logger.warning(f"Unsupported Content-Type for /process endpoint: {content_type}")
            raise HTTPException(status_code=400, detail=f"Unsupported Content-Type for /process endpoint: {content_type}. Use /process/pdf for PDF files.")

        # Route to action router if needed
        if result.get("action_triggered"):
            action_result = action_router.process(result)
            result["action_result"] = action_result

        return result

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/pdf")
async def process_pdf_input(file: UploadFile = File(...)):
    """Process PDF file input and route to the PDF agent."""
    logger.info(f"Received file for /process/pdf: {file.filename}, content_type: {file.content_type}")
    
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are supported on this endpoint.")
    
    try:
        content = await file.read()
        
        # Process PDF
        classification = classifier.process(content)
        if classification["format"] == "pdf":
            result = pdf_agent.process(content)
        else:
            # This case should ideally not be hit if classifier works correctly on PDF
            raise HTTPException(status_code=400, detail="Classifier did not identify input as PDF.")

        # Route to action router if needed
        if result.get("action_triggered"):
            action_result = action_router.process(result)
            result["action_result"] = action_result

        return result
        
    except Exception as e:
        logger.error(f"Error processing PDF file: {str(e)}")
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