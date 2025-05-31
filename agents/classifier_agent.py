from typing import Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .base_agent import BaseAgent

class ClassifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("classifier_agent")
        self.llm = ChatOpenAI(temperature=0)
        self.classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at classifying business documents and communications.
            Analyze the input and determine:
            1. The format (email, pdf, json)
            2. The business intent (RFQ, Invoice, Complaint, Regulation, Fraud Risk)
            
            Here are some examples:
            
            Example 1 (Email Complaint):
            Input: "From: customer@example.com\nSubject: Poor Service\n\nI am very unhappy with your service..."
            Output: {{"format": "email", "intent": "Complaint"}}
            
            Example 2 (JSON Webhook):
            Input: {{"event_type": "unauthorized_access", "timestamp": "2024-03-15T10:30:00Z"}}
            Output: {{"format": "json", "intent": "Fraud Risk"}}
            
            Example 3 (PDF Invoice):
            Input: "INVOICE #12345\nTotal Amount: $15,000.00\nDue Date: 2024-04-01"
            Output: {{"format": "pdf", "intent": "Invoice"}}
            
            Example 4 (Email RFQ):
            Input: "From: procurement@company.com\nSubject: Request for Quote\n\nWe are interested in purchasing..."
            Output: {{"format": "email", "intent": "RFQ"}}
            
            Example 5 (PDF Regulation):
            Input: "GDPR Compliance Policy\nEffective Date: 2024-01-01\nSection 1: Data Protection..."
            Output: {{"format": "pdf", "intent": "Regulation"}}
            
            Return your analysis in JSON format with 'format' and 'intent' fields."""),
            ("human", "Analyze this input: {input_text}")
        ])

    def process(self, input_data: Any) -> Dict[str, Any]:
        """Process input and classify its format and intent."""
        # Convert input to string if it's not already
        if isinstance(input_data, dict):
            input_text = json.dumps(input_data)
        else:
            input_text = str(input_data)

        # Get classification from LLM
        chain = self.classification_prompt | self.llm
        result = chain.invoke({"input_text": input_text})
        
        try:
            classification = json.loads(result.content)
            # Validate format
            if classification["format"] not in ["email", "pdf", "json"]:
                classification["format"] = "unknown"
            # Validate intent
            if classification["intent"] not in ["RFQ", "Invoice", "Complaint", "Regulation", "Fraud Risk"]:
                classification["intent"] = "unknown"
        except json.JSONDecodeError:
            # Fallback classification if LLM output isn't valid JSON
            classification = {
                "format": "unknown",
                "intent": "unknown"
            }

        # Log the classification with metadata
        self.log_activity(
            source="classifier",
            classification=classification,
            extracted_fields={
                "raw_input": input_text,
                "confidence": "high" if classification["format"] != "unknown" else "low"
            },
            agent_trace=["Format detection", "Intent analysis"]
        )

        return classification 